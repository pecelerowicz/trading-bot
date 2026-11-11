from decimal import Decimal

from binance import AsyncClient

from trading_bot.adapters.binance_executor import BinanceExecutor
from trading_bot.adapters.binance_market_data_source import (
    BinanceMarketDataSource,
)
from trading_bot.adapters.binance_rest_kline_mapper import (
    map_rest_kline,
)
from trading_bot.adapters.historical_kline_loader import (
    load_historical_klines,
)
from trading_bot.adapters.paper_executor import PaperExecutor
from trading_bot.adapters.replay_market_data_source import (
    ReplayMarketDataSource,
)
from trading_bot.config import (
    ExecutorConfig,
    InstrumentConfig,
    LiveConfig,
    ReplayConfig,
)
from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.ports.executor import Executor
from trading_bot.ports.market_data_source import MarketDataSource
from trading_bot.trading.debug_logger import TradingDebugLogger


async def build_market_data_source(
    runtime_mode: str,
    instrument_config: InstrumentConfig,
    live_config: LiveConfig,
    replay_config: ReplayConfig,
) -> tuple[MarketDataSource, AsyncClient | None]:
    if runtime_mode == "replay":
        klines = load_historical_klines(
            file_path=replay_config.file_path,
            mapper=map_rest_kline,
            initial_date=replay_config.initial_date,
            final_date=replay_config.final_date,
        )

        market_data_source = ReplayMarketDataSource(
            klines=klines,
            delay_seconds=replay_config.delay_seconds,
        )

        return market_data_source, None

    market_data_client = await AsyncClient.create(
        testnet=live_config.environment == "testnet",
    )

    market_data_source = BinanceMarketDataSource(
        client=market_data_client,
        symbol=instrument_config.symbol,
        interval=instrument_config.interval,
    )

    return market_data_source, market_data_client


async def build_executor(
    executor_config: ExecutorConfig,
    instrument: Instrument,
    logger: TradingDebugLogger,
) -> tuple[Executor, AsyncClient | None]:
    if executor_config.executor == "paper":
        initial_account = AccountSnapshot(
            balances=(
                AssetBalance(
                    asset=instrument.base_asset,
                    free=executor_config.paper_initial_base_balance,
                    locked=Decimal("0"),
                ),
                AssetBalance(
                    asset=instrument.quote_asset,
                    free=executor_config.paper_initial_quote_balance,
                    locked=Decimal("0"),
                ),
            )
        )

        executor = PaperExecutor(
            logger=logger,
            instrument=instrument,
            initial_account=initial_account,
        )

        return executor, None

    testnet = (
        executor_config.executor
        == "binance_testnet"
    )

    if testnet:
        api_key = (
            executor_config.binance_api_key_testnet
        )
        api_secret = (
            executor_config.binance_api_secret_testnet
        )
    else:
        api_key = (
            executor_config.binance_api_key_production
        )
        api_secret = (
            executor_config.binance_api_secret_production
        )

    executor_client = await AsyncClient.create(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
    )

    executor = BinanceExecutor(
        client=executor_client,
        instrument=instrument,
    )

    return executor, executor_client
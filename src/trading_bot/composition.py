from decimal import Decimal
from pathlib import Path

from binance import AsyncClient

from trading_bot.adapters.binance_executor import BinanceExecutor
from trading_bot.adapters.binance_market_data_source import BinanceMarketDataSource
from trading_bot.adapters.binance_rest_kline_mapper import map_rest_kline
from trading_bot.adapters.historical_kline_loader import load_historical_klines
from trading_bot.adapters.paper_executor import PaperExecutor
from trading_bot.adapters.replay_market_data_source import ReplayMarketDataSource
from trading_bot.config import ExecutorConfig, MarketDataConfig
from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.ports.executor import Executor
from trading_bot.ports.market_data_source import MarketDataSource
from trading_bot.trading.debug_logger import TradingDebugLogger


async def build_market_data_source(market_data_config: MarketDataConfig, instrument: Instrument) -> tuple[MarketDataSource, AsyncClient | None]:
    if market_data_config.market_data_source == "replay_binance":
        project_root = Path(__file__).resolve().parents[2]
        klines = load_historical_klines(
            file_path=project_root / "data" / "binance" / f"{instrument.symbol}_{market_data_config.interval}.json",
            mapper=map_rest_kline,
            initial_date=market_data_config.replay_initial_date,
            final_date=market_data_config.replay_final_date,
        )
        market_data_source = ReplayMarketDataSource(
            klines=klines,
            delay_seconds=market_data_config.replay_delay_seconds
        )
        return market_data_source, None

    market_data_client = await AsyncClient.create(testnet=market_data_config.market_data_source == "binance_testnet")
    market_data_source = BinanceMarketDataSource(
        client=market_data_client,
        symbol=instrument.symbol,
        interval=market_data_config.interval,
    )

    return market_data_source, market_data_client


async def build_executor(executor_config: ExecutorConfig, instrument: Instrument, logger: TradingDebugLogger) -> tuple[Executor, AsyncClient | None]:
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
        executor = PaperExecutor(logger=logger, instrument=instrument, initial_account=initial_account)
        return executor, None

    if executor_config.executor == "binance_testnet":
        api_key = executor_config.binance_api_key_testnet
        api_secret = executor_config.binance_api_secret_testnet
        testnet = True
    else:
        api_key = executor_config.binance_api_key_production
        api_secret = executor_config.binance_api_secret_production
        testnet = False

    executor_client = await AsyncClient.create(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
    )
    executor = BinanceExecutor(client=executor_client, instrument=instrument)

    return executor, executor_client
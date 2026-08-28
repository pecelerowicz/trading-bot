from decimal import Decimal

from binance import AsyncClient

from trading_bot.adapters.executor.binance.binance_executor import BinanceExecutor
from trading_bot.adapters.executor.paper.paper_executor import PaperExecutor
from trading_bot.adapters.market_data.binance.data_live.stream import BinanceMarketDataSource
from trading_bot.adapters.market_data.binance.data_replay.stream import BinanceReplayMarketDataSource
from trading_bot.config import AppConfig
from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.ports.executor import Executor
from trading_bot.ports.market_data_source import MarketDataSource
from trading_bot.trading.debug_logger import TradingDebugLogger


async def build_market_data_source(app_config: AppConfig) -> tuple[MarketDataSource, AsyncClient | None]:
    if app_config.market_data_source == "replay_binance":
        market_data_source = BinanceReplayMarketDataSource(
            symbol=app_config.symbol,
            interval=app_config.interval,
            initial_date=app_config.replay_initial_date,
            final_date=app_config.replay_final_date,
            delay_seconds=app_config.replay_delay_seconds
        )
        return market_data_source, None

    market_data_client = await AsyncClient.create(testnet=app_config.market_data_source == "binance_testnet")
    market_data_source = BinanceMarketDataSource(
        client=market_data_client,
        symbol=app_config.symbol,
        interval=app_config.interval,
    )

    return market_data_source, market_data_client


async def build_executor(app_config: AppConfig, instrument: Instrument, logger: TradingDebugLogger) -> tuple[Executor, AsyncClient | None]:
    if app_config.executor == "paper":
        initial_account = AccountSnapshot(
            balances=(
                AssetBalance(
                    asset=app_config.base_asset,
                    free=app_config.paper_initial_base_balance,
                    locked=Decimal("0"),
                ),
                AssetBalance(
                    asset=app_config.quote_asset,
                    free=app_config.paper_initial_quote_balance,
                    locked=Decimal("0"),
                ),
            )
        )
        executor = PaperExecutor(logger=logger, instrument=instrument, initial_account=initial_account)
        return executor, None

    if app_config.executor == "binance_testnet":
        api_key = app_config.binance_api_key_testnet
        api_secret = app_config.binance_api_secret_testnet
        testnet = True
    else:
        api_key = app_config.binance_api_key_production
        api_secret = app_config.binance_api_secret_production
        testnet = False

    executor_client = await AsyncClient.create(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
    )
    executor = BinanceExecutor(client=executor_client, instrument=instrument)

    return executor, executor_client
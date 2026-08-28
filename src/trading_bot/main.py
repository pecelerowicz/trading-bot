import asyncio
from decimal import Decimal

from binance import AsyncClient

from trading_bot.adapters.executor.binance.binance_executor import BinanceExecutor
from trading_bot.adapters.market_data.binance.data_live.stream import BinanceMarketDataSource
from trading_bot.adapters.market_data.binance.data_replay.stream import BinanceReplayMarketDataSource
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.three_green_pyramid_sell_strategy import ThreeGreenPyramidSellStrategy
from trading_bot.trading.trading_app import TradingApp
from trading_bot.config import load_app_config
from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.trading.trading_session import TradingSession
from trading_bot.adapters.executor.paper.paper_executor import PaperExecutor


async def main():
    app_config = load_app_config()

    #TODO instead having both Instrument and tuple (AssetBalance, AssetBalance), maybe it is possible to have one class only?
    #TODO my problem is that both Instrument and AssetBalance pull some of the same fields from configuration
    instrument = Instrument(symbol=app_config.symbol, base_asset=app_config.base_asset, quote_asset=app_config.quote_asset)
    strategy = ThreeGreenPyramidSellStrategy(instrument=instrument)
    logger = TradingDebugLogger()

    market_data_client: AsyncClient | None = None
    executor_client: AsyncClient | None = None

    try:
        if app_config.market_data_source == "replay_binance":
            market_data_source = BinanceReplayMarketDataSource(
                symbol=app_config.symbol,
                interval=app_config.interval,
                initial_date=app_config.replay_initial_date,
                final_date=app_config.replay_final_date,
                delay_seconds=app_config.replay_delay_seconds
            )
        else:
            market_data_client = await AsyncClient.create(testnet=app_config.market_data_source == "binance_testnet")
            market_data_source = BinanceMarketDataSource(
                client=market_data_client,
                symbol=app_config.symbol,
                interval=app_config.interval,
            )

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
        else:
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

        reconciliation_reporter = PortfolioReconciliationReporter(executor=executor, instrument=instrument)
        trading_session = TradingSession(strategy=strategy, executor=executor, logger=logger, reconciliation_reporter=reconciliation_reporter)

        app = TradingApp(
            market_data_source=market_data_source,
            trading_session=trading_session,
        )

        await app.run()

    finally:
        if market_data_client is not None:
            await market_data_client.close_connection()

        if executor_client is not None:
            await executor_client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from decimal import Decimal

from binance import AsyncClient

from trading_bot.adapters.executor.binance.binance_executor import BinanceExecutor
from trading_bot.adapters.market_data.binance.data_live.stream import BinanceMarketDataSource
from trading_bot.adapters.market_data.binance.data_replay.stream import LocalMarketDataSource
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
    strategy = ThreeGreenPyramidSellStrategy(instrument=instrument)
    logger = TradingDebugLogger()

    client: AsyncClient | None = None

    try:
        if app_config.is_mock:
            executor = PaperExecutor(logger=logger, instrument=instrument, initial_account=initial_account)
            market_data_source = LocalMarketDataSource(
                symbol=app_config.symbol,
                interval=app_config.interval,
                initial_date=app_config.mock_initial_date,
                final_date=app_config.mock_final_date,
                delay_seconds=app_config.mock_delay_seconds
            )
        else:
            client = await AsyncClient.create(
                api_key=app_config.api_key,
                api_secret=app_config.api_secret,
                testnet=app_config.is_testnet,
            )
            executor = BinanceExecutor(client=client, instrument=instrument)
            market_data_source = BinanceMarketDataSource(
                client=client,
                symbol=app_config.symbol,
                interval=app_config.interval,
            )

        reconciliation_reporter = PortfolioReconciliationReporter(executor=executor, instrument=instrument)
        trading_session = TradingSession(strategy=strategy, executor=executor, logger=logger, reconciliation_reporter=reconciliation_reporter)

        app = TradingApp(
            market_data_source=market_data_source,
            trading_session=trading_session,
        )

        await app.run()

    finally:
        if client is not None:
            await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
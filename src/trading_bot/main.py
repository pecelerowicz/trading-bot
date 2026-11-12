import asyncio

from trading_bot.composition import build_executor, build_market_data_source
from trading_bot.config import load_runtime_config
from trading_bot.models.instrument import Instrument
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import (
    PortfolioReconciliationReporter,
)
from trading_bot.trading.three_green_pyramid_sell_strategy import (
    ThreeGreenPyramidSellStrategy,
)
from trading_bot.trading.trading_app import TradingApp
from trading_bot.trading.trading_execution_service import TradingExecutionService
from trading_bot.trading.trading_session import TradingSession


async def main() -> None:
    runtime_config = load_runtime_config()

    instrument = Instrument(
        symbol=runtime_config.instrument.symbol,
        base_asset=runtime_config.instrument.base_asset,
        quote_asset=runtime_config.instrument.quote_asset,
    )

    strategy = ThreeGreenPyramidSellStrategy(
        instrument=instrument,
    )
    logger = TradingDebugLogger()

    market_data_client = None
    executor_client = None

    try:
        market_data_source, market_data_client = await build_market_data_source(
            source_config=runtime_config.source_config,
            instrument_config=runtime_config.instrument,
        )

        executor, executor_client = await build_executor(
            executor_config=runtime_config.executor_config,
            instrument=instrument,
            logger=logger,
        )

        execution_service = TradingExecutionService(
            executor=executor,
            logger=logger,
        )

        reconciliation_reporter = PortfolioReconciliationReporter(
            executor=executor,
            instrument=instrument,
        )

        trading_session = TradingSession(
            strategy=strategy,
            execution_service=execution_service,
            logger=logger,
            reconciliation_reporter=reconciliation_reporter,
        )

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
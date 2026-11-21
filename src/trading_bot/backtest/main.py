import asyncio

from trading_bot.backtest.app import BacktestApp
from trading_bot.composition import (
    build_executor,
    load_historical_market_data,
)
from trading_bot.config.backtest import load_backtest_config
from trading_bot.models.instrument import Instrument
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import (
    PortfolioReconciliationReporter,
)
from trading_bot.trading.three_green_pyramid_sell_strategy import (
    ThreeGreenPyramidSellStrategy,
)
from trading_bot.trading.trading_execution_service import TradingExecutionService
from trading_bot.trading.trading_session import TradingSession


async def main() -> None:
    backtest_config = load_backtest_config()

    instrument = Instrument(
        symbol=backtest_config.instrument.symbol,
        base_asset=backtest_config.instrument.base_asset,
        quote_asset=backtest_config.instrument.quote_asset,
    )

    strategy = ThreeGreenPyramidSellStrategy(instrument=instrument)
    logger = TradingDebugLogger()

    klines = load_historical_market_data(
        historical_data=backtest_config.historical_data,
    )

    executor = await build_executor(
        executor_config=backtest_config.executor_config,
        instrument=instrument,
        logger=logger,
    )

    execution_service = TradingExecutionService(executor=executor, logger=logger)

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

    app = BacktestApp(
        klines=klines,
        trading_session=trading_session,
    )

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
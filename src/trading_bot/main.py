import asyncio

from trading_bot.adapters.market_data.binance.data_live.stream import BinanceMarketDataSource
from trading_bot.adapters.market_data.binance.data_replay.stream import LocalMarketDataSource
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.three_green_pyramid_sell_strategy import ThreeGreenPyramidSellStrategy
from trading_bot.trading.trading_app import TradingApp
from trading_bot.config import load_app_config
from trading_bot.trading.trading_session import TradingSession
from trading_bot.adapters.execution.paper.paper_executor import PaperExecutor
from trading_bot.trading.green_red_strategy import GreenRedStrategy


async def main():
    app_config = load_app_config()

    # strategy = GreenRedStrategy()
    strategy = ThreeGreenPyramidSellStrategy()
    debug_logger = TradingDebugLogger()

    executor = PaperExecutor(debug_logger=debug_logger)

    trading_session = TradingSession(
        strategy=strategy,
        executor=executor,
        debug_logger=debug_logger,
    )

    if app_config.is_mock:
        market_data_source = LocalMarketDataSource(
            symbol=app_config.symbol,
            interval=app_config.interval,
            initial_date=app_config.mock_initial_date,
            final_date=app_config.mock_final_date,
            delay_seconds=app_config.mock_delay_seconds,
        )
    else:
        market_data_source = BinanceMarketDataSource(
            api_key=app_config.api_key,
            api_secret=app_config.api_secret,
            testnet=not app_config.is_production,
            symbol=app_config.symbol,
            interval=app_config.interval,
        )

    app = TradingApp(
        market_data_source=market_data_source,
        trading_session=trading_session,
    )

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
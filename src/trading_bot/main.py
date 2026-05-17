import asyncio

from trading_bot.apps.binance_app import BinanceApp
from trading_bot.apps.mock_app import MockApp
from trading_bot.config import load_app_config
from trading_bot.trading.trading_session import TradingSession
from trading_bot.trading.paper_executor import PaperExecutor
from trading_bot.trading.green_red_strategy import GreenRedStrategy


async def main():
    app_config = load_app_config()
    strategy = GreenRedStrategy()
    executor = PaperExecutor()

    trading_session = TradingSession(strategy=strategy, executor=executor)

    if app_config.is_mock:
        app = MockApp(app_config=app_config, trading_session=trading_session)
    else:
        app = BinanceApp(app_config=app_config, trading_session=trading_session)

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
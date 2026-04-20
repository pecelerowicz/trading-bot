from dotenv import load_dotenv
import os
import asyncio

from trading_bot.apps.binance_app import BinanceApp
from trading_bot.apps.mock_app import MockApp

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_MOCK = False


async def main():
    print("Hello trading bot")

    if USE_MOCK:
        app = MockApp()
    else:
        app = BinanceApp(API_KEY, API_SECRET, "BTCUSDT", '1h')

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
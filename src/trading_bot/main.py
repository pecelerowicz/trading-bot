from dotenv import load_dotenv
import os
import asyncio

from trading_bot.apps.binance_app import BinanceApp
from trading_bot.apps.mock_app import MockApp

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
use_mock = os.getenv("USE_MOCK", "false").lower() == "true"


async def main():
    print("Hello trading bot")

    if use_mock:
        # TODO it should throw an exception if the data range is not within what is available in the raw data
        app = MockApp(symbol='BTCUSDT', interval="1h", initial_date="2023-01-01", final_date="2024-01-02", delay_seconds=1.0)
    else:
        app = BinanceApp(api_key=api_key, api_secret=api_secret, symbol="BTCUSDT", interval='1h')

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
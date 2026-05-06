from dotenv import load_dotenv
import os
import asyncio

from trading_bot.apps.binance_app import BinanceApp
from trading_bot.apps.mock_app import MockApp
from trading_bot.trading.trading_session import TradingSession

load_dotenv()

binance_env = os.getenv("BINANCE_ENV")
valid_environments = {"mock", "testnet", "production"}

if binance_env not in valid_environments:
    raise ValueError(
        f"Invalid BINANCE_ENV={binance_env!r}. "
        f"Expected one of: {', '.join(sorted(valid_environments))}"
    )

api_key = None
api_secret = None
#use_mock = binance_env == "mock"
#use_testnet = binance_env == "testnet"

if binance_env == "mock":
    api_key = None
    api_secret = None

elif binance_env == "testnet":
    api_key = os.getenv("BINANCE_API_KEY_TESTNET")
    api_secret = os.getenv("BINANCE_API_SECRET_TESTNET")

elif binance_env == "production":
    api_key = os.getenv("BINANCE_API_KEY_PRODUCTION")
    api_secret = os.getenv("BINANCE_API_SECRET_PRODUCTION")

async def main():
    print("Hello trading bot")

    trading_session = TradingSession()

    if binance_env == "mock":
        # TODO it should throw an exception if the data range is not within what is available in the raw data
        app = MockApp(symbol='BTCUSDT', interval="1m", initial_date="2023-01-01", final_date="2024-01-02",
                      delay_seconds=1.0, trading_session=trading_session)
    else:
        use_production = binance_env == "production"
        app = BinanceApp(api_key=api_key, api_secret=api_secret, symbol="BTCUSDT", interval='1m',
                         trading_session=trading_session, use_production=use_production)

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
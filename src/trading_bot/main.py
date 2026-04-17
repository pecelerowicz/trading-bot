from dotenv import load_dotenv
import os
import asyncio
import pandas as pd

from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException, BinanceRequestException

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")


async def handle_message(async_client, msg):
    event_time = pd.to_datetime(msg["E"], unit="ms")
    price = float(msg["c"])

    print(f"Time: {event_time} | Price: {price}")

    if int(price) % 10 == 0:
        try:
            order = await async_client.create_order(
                symbol="BTCUSDT",
                side="SELL",
                type="MARKET",
                quantity=0.1
            )

            print("\n" + "-" * 50)
            print(
                f"Sell {order['executedQty']} BTC for {order['cummulativeQuoteQty']} USDT"
            )
            print("-" * 50 + "\n")

            return True  # sygnał do zatrzymania streamu

        except (BinanceAPIException, BinanceRequestException) as e:
            print(f"Order error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    return False


async def main():
    print("Hello trading bot")

    async_client = await AsyncClient.create(
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=True
    )

    bm = BinanceSocketManager(async_client)
    ts = bm.symbol_miniticker_socket(symbol="BTCUSDT")

    try:
        async with ts as stream:
            while True:
                msg = await stream.recv()
                should_stop = await handle_message(async_client, msg)
                if should_stop:
                    break
    finally:
        await async_client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
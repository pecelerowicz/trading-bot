import pandas as pd
from binance.exceptions import BinanceAPIException, BinanceRequestException


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

            return True

        except (BinanceAPIException, BinanceRequestException) as e:
            print(f"Order error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    return False


async def handle_message_print(msg):
    print(msg)
    return False
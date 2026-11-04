from decimal import Decimal

from binance import Client

from scripts.binance_account_and_order_api import BinanceAccountAndOrderApi
from scripts.binance_market_data_api import BinanceMarketDataApi
from trading_bot.config import load_runtime_config


def main():

    runtime_config = load_runtime_config()

    if runtime_config.executor.executor != "binance_testnet":
        raise ValueError("account_and_orders.py requires Binance testnet executor")

    client = Client(
        api_key=runtime_config.executor.binance_api_key_testnet,
        api_secret=runtime_config.executor.binance_api_secret_testnet,
        testnet=True,
    )

    executor = BinanceAccountAndOrderApi(client=client)
    retriever = BinanceMarketDataApi(client=client)

    # get_balance
    print("--- get_balance ---")
    print(executor.get_balance("BTC"))
    print(executor.get_balance("USDT"))
    print(executor.get_balance("ETH"))
    print(executor.get_balance("SOL"))
    print(executor.get_balance("ADA"))
    print(executor.get_balance("MATIC"))
    print(executor.get_balance("DOT"))
    print(executor.get_balance("PEPE"))
    print(executor.get_balance("ONDO"))
    print(executor.get_balance("LINK"))
    print(executor.get_balance("XRP"))

    # get_current_price
    print("--- get_current_price ---")
    print(retriever.get_current_price("BTCUSDT"))

    # buy_market_quantity
    print("--- buy_market_quantity ---")
    print(executor.buy_market_quantity("BTCUSDT", Decimal("1.0")))

    # get_open_orders
    print("--- get_open_orders ---")
    print(executor.get_open_orders("BTCUSDT"))

    # get_balance
    print("--- get_balance ---")
    print(executor.get_balance("BTC"))
    print(executor.get_balance("USDT"))


if __name__ == "__main__":
    main()
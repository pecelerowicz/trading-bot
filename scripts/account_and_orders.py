from decimal import Decimal

from binance import Client

from scripts.api import BinanceOrderApi
from trading_bot.adapters.market_data.binance.data_live.api import BinanceMarketDataApi
from trading_bot.config import load_app_config


def main():

    app_config = load_app_config()
    client = Client(api_key=app_config.api_key, api_secret=app_config.api_secret, testnet=app_config.is_testnet) # tu już jest problem, bo dla mock wybierze production
    executor = BinanceOrderApi(client=client)
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

    # # buy_limit_quantity
    # print("--- buy_limit_quantity ---")
    # print(executor.buy_market_quantity("BTCUSDT", Decimal("1")))
    # executor.sell_market_quantity("SOLUSDT", Decimal("6"))
    # executor.sell_market_quantity("PEPEUSDT", Decimal("18446"))
    # executor.sell_market_quantity("ONDOUSDT", Decimal("1313"))
    # executor.sell_market_quantity("LINKUSDT", Decimal("61"))
    # executor.sell_market_quantity("XRPUSDT", Decimal("470"))



    # get_open_orders
    print("--- get_open_orders ---")
    print(executor.get_open_orders("BTCUSDT"))


    # get_balance
    print("--- get_balance ---")
    print(executor.get_balance("SOL"))
    print(executor.get_balance("USDT"))

if __name__ == "__main__":
    main()

from decimal import Decimal

from binance import Client
from trading_bot.config import load_app_config
from trading_bot.trading.binance_executor import BinanceExecutor

def main():

    app_config = load_app_config()
    client = Client(api_key=app_config.api_key, api_secret=app_config.api_secret, testnet=app_config.is_testnet) # tu już jest problem, bo dla mock wybierze production
    executor = BinanceExecutor(client)

    # get_balance
    print("--- get_balance ---")
    print(executor.get_balance("SOL"))
    print(executor.get_balance("USDT"))

    # # buy_market_qty
    # print("--- buy_market_qty ---")
    # order = executor.buy_market_qty("SOLUSDT", 1)
    # print(order)
    # print("---")
    # print(executor.get_balance("SOL"))
    # print(executor.get_balance("USDT"))
    #
    # # sell_market_qty
    # print("--- sell_market_qty ---")
    # order = executor.sell_market_qty("SOLUSDT", 1)
    # print(order)
    # print("---")
    # print(executor.get_balance("SOL"))
    # print(executor.get_balance("USDT"))

    # executor.sell_market_quantity("SOLUSDT", Decimal("1.10400000"))
    # print(executor.get_current_price("SOLUSDT"))
    # executor.get_balance("SOL")


if __name__ == "__main__":
    main()

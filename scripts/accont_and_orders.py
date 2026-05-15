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

    # get_current_price
    print("--- get_current_price ---")
    print(executor.get_current_price("SOLUSDT"))

    # # buy_limit_quantity
    # print("--- buy_limit_quantity ---")
    # print(executor.buy_limit_quantity("SOLUSDT", Decimal("1"), Decimal("91")))
    # print(executor.sell_limit_quantity("SOLUSDT", Decimal("1"), Decimal("92")))

    # get_open_orders
    print("--- get_open_orders ---")
    print(executor.get_open_orders("SOLUSDT"))


if __name__ == "__main__":
    main()

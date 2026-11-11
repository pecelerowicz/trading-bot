import os
from decimal import Decimal
from pathlib import Path

from binance import Client
from dotenv import load_dotenv

from scripts.binance_account_and_order_api import BinanceAccountAndOrderApi
from scripts.binance_market_data_api import BinanceMarketDataApi


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    client = Client(
        api_key=_get_required_env_var(
            "BINANCE_API_KEY_TESTNET"
        ),
        api_secret=_get_required_env_var(
            "BINANCE_API_SECRET_TESTNET"
        ),
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


def _get_required_env_var(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(f"{name} is required")

    return value.strip()


if __name__ == "__main__":
    main()
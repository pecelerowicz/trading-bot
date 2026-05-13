from decimal import Decimal
from typing import Literal

BalanceAmountType = Literal["free", "locked", "total"]

class BinanceExecutor:
    def __init__(self, client):
        self.client = client

    def get_balance(self, asset: str, asset_type: Literal["free", "locked", "total"] | None = None):
        balance = self.client.get_asset_balance(asset=asset)

        if balance is None:
            balance = {
                "asset": asset,
                "free": "0",
                "locked": "0",
            }

        if asset_type is None:
            return balance

        free = Decimal(balance["free"])
        locked = Decimal(balance["locked"])

        if asset_type == "free":
            return free

        if asset_type == "locked":
            return locked

        if asset_type == "total":
            return free + locked

        raise ValueError(f"Invalid amount_type: {asset_type}")

    def buy_market_qty(self, symbol: str, quantity):
        return self.client.create_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quantity=quantity,
        )

    def buy_market_quote(self, symbol: str, quote_amount):
        pass

    def sell_market_qty(self, symbol: str, quantity):
        pass

    def sell_market_quote(self, symbol: str, quote_amount):
        pass

    def buy_limit_qty(self, symbol: str, quantity, price):
        pass

    def buy_limit_quote(self, symbol: str, quote_amount, price):
        pass

    def sell_limit_qty(self, symbol: str, quantity, price):
        pass

    def sell_limit_quote(self, symbol: str, quote_amount, price):
        pass

    def get_open_orders(self, symbol: str):
        pass

    def cancel_open_orders(self, symbol: str):
        pass
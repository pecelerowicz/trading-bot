from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal


BalanceType = Literal["free", "locked", "total"]


@dataclass(frozen=True)
class OrderResult:
    symbol: str
    order_id: int
    side: str
    status: str
    requested_qty: Decimal
    executed_qty: Decimal
    executed_quote_qty: Decimal
    avg_price: Decimal | None
    raw: dict[str, Any]


class BinanceExecutor:
    def __init__(self, client):
        self.client = client

    def get_balance(self, asset: str, balance_type: BalanceType | None = None) -> dict[str, Any] | Decimal:
        balance = self.client.get_asset_balance(asset=asset)

        if balance is None:
            balance = {
                "asset": asset,
                "free": "0",
                "locked": "0",
            }

        if balance_type is None:
            return balance

        free = Decimal(balance["free"])
        locked = Decimal(balance["locked"])

        if balance_type == "free":
            return free

        if balance_type == "locked":
            return locked

        if balance_type == "total":
            return free + locked

        raise ValueError(f"Invalid balance_type: {balance_type}")

    def buy_market_quantity(self, symbol: str, quantity: Decimal) -> OrderResult:
        order = self.client.create_order(symbol=symbol, side="BUY", type="MARKET", quantity=str(quantity))
        return self._map_order(order)

    def buy_market_quote(self, symbol: str, quote: Decimal) -> OrderResult:
        order = self.client.create_order(symbol=symbol, side="BUY", type="MARKET", quoteOrderQty=str(quote))
        return self._map_order(order)

    def sell_market_quantity(self, symbol: str, quantity: Decimal) -> OrderResult:
        order = self.client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=str(quantity))
        return self._map_order(order)

    def sell_market_quote(self, symbol: str, quote: Decimal) -> OrderResult:
        order = self.client.create_order(symbol=symbol, side="SELL", type="MARKET", quoteOrderQty=str(quote))
        return self._map_order(order)

    def buy_limit_quantity(self, symbol: str, quantity: Decimal, price: Decimal) -> OrderResult:
        order = self.client.create_order(symbol=symbol, side="BUY", type="LIMIT", timeInForce="GTC",
                                         quantity=str(quantity), price=str(price))
        return self._map_order(order)

    def buy_limit_quote(self, symbol: str, quote: Decimal, price: Decimal) -> OrderResult:
        quantity = quote / price
        return self.buy_limit_quantity(symbol=symbol, quantity=quantity, price=price)

    def sell_limit_quantity(self, symbol: str, quantity: Decimal, price: Decimal) -> OrderResult:
        order = self.client.create_order(symbol=symbol, side="SELL", type="LIMIT", timeInForce="GTC",
                                         quantity=str(quantity), price=str(price))
        return self._map_order(order)

    def sell_limit_quote(self, symbol: str, quote: Decimal, price: Decimal) -> OrderResult:
        quantity = quote / price
        return self.sell_limit_quantity(symbol, quantity, price)

    def get_open_orders(self, symbol: str) -> list[dict[str, Any]]:
        return self.client.get_open_orders(symbol=symbol)

    def cancel_open_orders(self, symbol: str) -> list[dict[str, Any]]:
        orders = self.get_open_orders(symbol)
        cancelled_orders = []
        for order in orders:
            cancelled_order = self.client.cancel_order(
                symbol=symbol,
                orderId=order["orderId"],
            )
            cancelled_orders.append(cancelled_order)
        return cancelled_orders

    def get_current_price(self, symbol: str) -> Decimal:
        # TODO: This method is only for temporary diagnostics.
        # In the target architecture, price data should come from the market data stream
        # or be moved to a separate MarketData/BinanceMarketData class.
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return Decimal(ticker["price"])

    def _map_order(self, order: dict[str, Any]) -> OrderResult:
        executed_qty = Decimal(order.get("executedQty", "0"))
        executed_quote_qty = Decimal(order.get("cummulativeQuoteQty", "0"))

        avg_price = None
        if executed_qty > 0:
            avg_price = executed_quote_qty / executed_qty

        return OrderResult(
            symbol=order["symbol"],
            order_id=order["orderId"],
            side=order["side"],
            status=order["status"],
            requested_qty=Decimal(order.get("origQty", "0")),
            executed_qty=executed_qty,
            executed_quote_qty=executed_quote_qty,
            avg_price=avg_price,
            raw=order,
        )

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

import pandas as pd


class BinanceMarketDataRetriever:
    def __init__(self, client):
        self.client = client

    def _to_timestamp(self, date_str: str) -> int:
        dt = pd.to_datetime(date_str, utc=True)
        return dt.value // 10**6

    def _interval_to_ms(self, interval: str) -> int:
        mapping = {
            "1d": 86_400_000,
            "4h": 14_400_000,
            "1h": 3_600_000,
            "1m": 60_000
        }
        if interval not in mapping:
            raise ValueError(f"Unsupported interval: {interval}")
        return mapping[interval]

    def get_current_price(self, symbol: str) -> Decimal:
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return Decimal(ticker["price"])

    # TODO this run up is probably to be removed from here (and moved to the mock streamer)
    def get_raw_klines(
        self,
        symbol: str,
        interval: str,
        initial_date: str,
        final_date: str,
        run_up: int = 0,
    ) -> list[list]:
        if run_up < 0:
            raise ValueError("run_up cannot be negative")

        offset = self._interval_to_ms(interval) * run_up
        start_ts = self._to_timestamp(initial_date) - offset
        end_ts = self._to_timestamp(final_date)

        return self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_ts,
            end_str=end_ts,
        )

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
    raw: dict[str, Any] | None = None

class BinanceOrderExecutor:
    def __init__(self, client, include_raw: bool = False):
        self.client = client
        self.include_raw = include_raw

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

    def get_open_orders(self, symbol: str) -> list[OrderResult]:
        orders = self.client.get_open_orders(symbol=symbol)
        return [self._map_order(order) for order in orders]

    def cancel_order(self, symbol: str, order_id: int) -> OrderResult:
        cancelled_order = self.client.cancel_order(
            symbol=symbol,
            orderId=order_id,
        )
        return self._map_order(cancelled_order)

    def cancel_open_orders(self, symbol: str) -> list[OrderResult]:
        orders = self.client.get_open_orders(symbol=symbol)
        cancelled_orders = []

        for order in orders:
            cancelled_orders.append(
                self.cancel_order(symbol=symbol, order_id=order["orderId"])
            )

        return cancelled_orders

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
            raw=order if self.include_raw else None
        )
from dataclasses import dataclass

from trading_bot.trading.order import Order


@dataclass
class Trade:
    reason: str
    orders: list[Order]

    @property
    def buy_filled_quantity(self) -> float:
        return sum(
            order.filled_quantity
            for order in self.orders
            if order.request.side == "BUY"
        )

    @property
    def sell_filled_quantity(self) -> float:
        return sum(
            order.filled_quantity
            for order in self.orders
            if order.request.side == "SELL"
        )

    @property
    def net_quantity(self) -> float:
        return self.buy_filled_quantity - self.sell_filled_quantity

    @property
    def has_open_orders(self) -> bool:
        return any(
            order.status in {"NEW", "PARTIALLY_FILLED"}
            for order in self.orders
        )

    @property
    def is_flat(self) -> bool:
        return self.net_quantity <= 0
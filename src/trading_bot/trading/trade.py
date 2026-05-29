from dataclasses import dataclass

from trading_bot.trading.order import Order


@dataclass
class Trade:
    reason: str
    orders: list[Order]

    @property
    def filled_quantity(self) -> float:
        return sum(order.filled_quantity for order in self.orders)

    @property
    def has_any_fill(self) -> bool:
        return self.filled_quantity > 0

    @property
    def has_open_orders(self) -> bool:
        return any(
            order.status in {"NEW", "PARTIALLY_FILLED"}
            for order in self.orders
        )
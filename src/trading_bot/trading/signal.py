from dataclasses import dataclass

from trading_bot.trading.order import OrderRequest


@dataclass(frozen=True)
class StrategyAction:
    reason: str
    order_requests: list[OrderRequest]

    @property
    def has_orders(self) -> bool:
        return len(self.order_requests) > 0
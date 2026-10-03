from dataclasses import dataclass
from enum import Enum

from trading_bot.models.order import OrderRequest


class SignalType(Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"


@dataclass(frozen=True)
class StrategySignal:
    signal_type: SignalType
    cancel_order_ids: list[str]
    order_requests: list[OrderRequest]

    def __post_init__(self) -> None:
        if self.signal_type == SignalType.OPEN and self.cancel_order_ids:
            raise ValueError("Open signal cannot cancel orders")

        if self.signal_type == SignalType.CLOSE and any(order_request.order_type != "MARKET" for order_request in self.order_requests):
            raise ValueError("Close signal supports only MARKET orders")
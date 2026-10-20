from dataclasses import dataclass
from enum import Enum

from trading_bot.models.order import OrderRequest


class SignalType(Enum):
    IDLE = "IDLE"
    OPEN = "OPEN"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


@dataclass(frozen=True)
class StrategySignal:
    signal_type: SignalType
    cancel_order_ids: list[str]
    order_requests: list[OrderRequest]

    def __post_init__(self) -> None:
        if self.signal_type in {SignalType.IDLE, SignalType.HOLD}:
            if self.cancel_order_ids or self.order_requests:
                raise ValueError(
                    f"{self.signal_type.value} signal cannot contain order operations"
                )

        if self.signal_type == SignalType.OPEN and self.cancel_order_ids:
            raise ValueError("Open signal cannot cancel orders")

        if self.signal_type == SignalType.CLOSE and any(
            order_request.order_type != "MARKET"
            for order_request in self.order_requests
        ):
            raise ValueError("Close signal supports only MARKET orders")

    @classmethod
    def idle(cls) -> "StrategySignal":
        return cls(
            signal_type=SignalType.IDLE,
            cancel_order_ids=[],
            order_requests=[],
        )

    @classmethod
    def open_campaign(
        cls,
        order_requests: list[OrderRequest],
    ) -> "StrategySignal":
        return cls(
            signal_type=SignalType.OPEN,
            cancel_order_ids=[],
            order_requests=order_requests,
        )

    @classmethod
    def hold_campaign(cls) -> "StrategySignal":
        return cls(
            signal_type=SignalType.HOLD,
            cancel_order_ids=[],
            order_requests=[],
        )

    @classmethod
    def close_campaign(
        cls,
        cancel_order_ids: list[str],
        order_requests: list[OrderRequest],
    ) -> "StrategySignal":
        return cls(
            signal_type=SignalType.CLOSE,
            cancel_order_ids=cancel_order_ids,
            order_requests=order_requests,
        )
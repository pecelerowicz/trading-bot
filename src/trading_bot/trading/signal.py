from dataclasses import dataclass, field

from trading_bot.models.order import Order, OrderRequest
from trading_bot.ports.executor import ExecutorResult


@dataclass(frozen=True)
class OpenCampaign:
    order_requests: list[OrderRequest]


@dataclass(frozen=True)
class CloseCampaign:
    order_requests: list[OrderRequest]

    def __post_init__(self) -> None:
        if any(order_request.order_type != "MARKET" for order_request in self.order_requests):
            raise ValueError("CloseCampaign supports only MARKET orders")


@dataclass(frozen=True)
class NoAction:
    pass


StrategySignal = OpenCampaign | CloseCampaign | NoAction


@dataclass
class SignalExecution:
    order_results: list[ExecutorResult[Order]] = field(default_factory=list)
from dataclasses import dataclass
from typing import TypeAlias

from trading_bot.models.order import OrderRequest


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


StrategySignal: TypeAlias = OpenCampaign | CloseCampaign | NoAction
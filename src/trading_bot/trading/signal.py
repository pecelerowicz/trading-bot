from dataclasses import dataclass, field
from typing import TypeAlias

from trading_bot.models.order import OrderRequest


@dataclass(frozen=True)
class OpenCampaign:
    order_requests: list[OrderRequest]


@dataclass(frozen=True)
class CloseCampaign:
    order_requests: list[OrderRequest]
    order_ids_to_cancel: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NoAction:
    pass


StrategySignal: TypeAlias = OpenCampaign | CloseCampaign | NoAction
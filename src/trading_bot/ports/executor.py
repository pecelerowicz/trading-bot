from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest

T = TypeVar("T")


class ExecutorResultStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExecutorResult(Generic[T]):
    status: ExecutorResultStatus
    value: T | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if self.status == ExecutorResultStatus.SUCCESS and self.value is None:
            raise ValueError("Successful executor result requires a value")

        if self.status != ExecutorResultStatus.SUCCESS and self.value is not None:
            raise ValueError("Failed or unknown executor result cannot contain a value")


class Executor(Protocol):
    # TODO: Revisit whether update_executor belongs in the common port after BinanceExecutor is implemented.
    async def update_executor(self, kline: KlineEvent) -> None:
        ...

    async def place_order(self, order_request: OrderRequest) -> ExecutorResult[Order]:
        ...

    async def get_order(self, order_id: str) -> ExecutorResult[Order]:
        ...

    async def cancel_order(self, order_id: str) -> ExecutorResult[Order]:
        ...

    async def get_account_snapshot(self) -> AccountSnapshot:
        ...
from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest


class Executor(Protocol):
    # TODO: Revisit whether update_executor belongs in the common port after BinanceExecutor is implemented.
    async def update_executor(self, kline: KlineEvent) -> None:
        ...

    async def place_order(self, order_request: OrderRequest) -> Order:
        ...

    async def sync_order_status(self, order: Order) -> Order:
        ...

    async def cancel_order(self, order: Order) -> Order:
        ...

    async def get_account_snapshot(self) -> AccountSnapshot:
        ...
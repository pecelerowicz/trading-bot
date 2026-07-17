from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest


class Executor(Protocol):
    async def process_kline(self, kline: KlineEvent) -> None:
        ...

    async def place_order(self, order_request: OrderRequest) -> Order:
        ...

    async def sync_order_status(self, order: Order, kline: KlineEvent) -> Order:
        ...

    async def cancel_order(self, order: Order) -> Order:
        ...

    async def get_account_snapshot(self) -> AccountSnapshot:
        ...
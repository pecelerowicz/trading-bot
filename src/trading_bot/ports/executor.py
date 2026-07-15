from typing import Protocol

from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import Order, OrderRequest


class Executor(Protocol):
    async def place_order(
        self,
        order_request: OrderRequest,
        kline: KlineEvent,
    ) -> Order:
        ...

    async def sync_order_status(
        self,
        order: Order,
        kline: KlineEvent,
    ) -> Order:
        ...

    async def cancel_order(
        self,
        order: Order,
    ) -> Order:
        ...
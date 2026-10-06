from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest

class Executor(Protocol):
    # TODO: Revisit whether update_executor belongs in the common port after BinanceExecutor is implemented.
    async def update_executor(self, kline: KlineEvent) -> None:
        ...

    async def place_order(self, order_request: OrderRequest) -> Order:
        """
        Place a new order.

        Returns:
            The order created by the executor.

        Raises:
            OrderRejectedError:
                If the order is definitively rejected and no order is created.
            OrderPlacementOutcomeUnknownError:
                If the order request was sent, but it cannot be determined whether the order was created.
        """
        ...

    async def get_order(self, order_id: str) -> Order:
        ...

    async def cancel_order(self, order_id: str) -> Order:
        ...

    async def get_account_snapshot(self) -> AccountSnapshot:
        ...
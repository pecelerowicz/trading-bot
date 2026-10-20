from trading_bot.errors import (
    OrderCancellationOutcomeUnknownError,
    OrderCancellationRejectedError,
    OrderNotFoundError,
    OrderPlacementOutcomeUnknownError,
    OrderPlacementRejectedError,
)
from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import OrderStateSnapshot
from trading_bot.models.execution import (
    Cancellation,
    Execution,
    OperationStatus,
    Placement,
)
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest
from trading_bot.ports.executor import Executor
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.signal import StrategySignal


class TradingExecutionService:

    def __init__(self, executor: Executor, logger: TradingDebugLogger) -> None:
        self.executor = executor
        self.logger = logger

    async def update_executor(self, kline: KlineEvent) -> None:
        await self.executor.update_executor(kline)

    async def get_account_snapshot(self) -> AccountSnapshot:
        return await self.executor.get_account_snapshot()

    async def get_order_state_snapshot(self, order_ids: list[str]) -> OrderStateSnapshot:
        orders: list[Order] = []

        for order_id in order_ids:
            order = await self.executor.get_order(order_id)
            orders.append(order)

        return OrderStateSnapshot(orders=tuple(orders))

    async def execute_signal(self, signal: StrategySignal) -> Execution:
        cancellations: list[Cancellation] = []
        placements: list[Placement] = []

        for index, order_id in enumerate(signal.cancel_order_ids):
            cancellation = await self._execute_cancellation(order_id)
            cancellations.append(cancellation)

            if cancellation.status != "SUCCESS":
                remaining_order_ids = signal.cancel_order_ids[index + 1:]

                for remaining_order_id in remaining_order_ids:
                    cancellations.append(Cancellation(order_id=remaining_order_id, status="NOT_EXECUTED"))

                for order_request in signal.order_requests:
                    placements.append(Placement(order_request=order_request, status="NOT_EXECUTED"))

                return Execution(cancellations=tuple(cancellations), placements=tuple(placements))

        for index, order_request in enumerate(signal.order_requests):
            placement = await self._execute_placement(order_request)
            placements.append(placement)

            if placement.status != "SUCCESS":
                remaining_order_requests = signal.order_requests[index + 1:]

                for remaining_order_request in remaining_order_requests:
                    placements.append(Placement(order_request=remaining_order_request, status="NOT_EXECUTED"))

                return Execution(cancellations=tuple(cancellations), placements=tuple(placements))

        return Execution(cancellations=tuple(cancellations), placements=tuple(placements))

    async def _execute_cancellation(self, order_id: str) -> Cancellation:
        try:
            order = await self.executor.cancel_order(order_id)

        except (OrderNotFoundError, OrderCancellationRejectedError):
            return Cancellation(order_id=order_id, status="FAILURE")

        except OrderCancellationOutcomeUnknownError:
            return Cancellation(order_id=order_id, status="UNKNOWN")

        if order.status != "CANCELED":
            return Cancellation(order_id=order_id, status="UNEXPECTED_RESULT", order=order)

        return Cancellation(order_id=order_id, status="SUCCESS", order=order)

    async def _execute_placement(self, order_request: OrderRequest) -> Placement:
        try:
            order = await self.executor.place_order(order_request)

        except OrderPlacementRejectedError:
            return Placement(order_request=order_request, status="FAILURE")

        except OrderPlacementOutcomeUnknownError:
            return Placement(order_request=order_request, status="UNKNOWN")

        return Placement(order_request=order_request, status=self._placement_status(order), order=order)

    def _placement_status(self, order: Order) -> OperationStatus:
        if order.order_type == "MARKET":
            if order.status == "FILLED":
                return "SUCCESS"

            return "UNEXPECTED_RESULT"

        if order.order_type == "LIMIT":
            if order.status in {"NEW", "PARTIALLY_FILLED", "FILLED"}:
                return "SUCCESS"

            return "UNEXPECTED_RESULT"

        return "UNEXPECTED_RESULT"
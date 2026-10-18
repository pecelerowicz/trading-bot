from trading_bot.errors import (
    MarketOrderNotFullyFilledError,
    OrderCancellationNotCompletedError,
    StrategySignalConflictError,
    UnexpectedOrderStateError,
)
from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import Campaign, CampaignView
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest
from trading_bot.ports.executor import Executor
from trading_bot.trading.debug_logger import TradingDebugLogger


class TradingExecutionService:

    def __init__(self, executor: Executor, logger: TradingDebugLogger) -> None:
        self.executor = executor
        self.logger = logger

    async def update_executor(self, kline: KlineEvent) -> None:
        await self.executor.update_executor(kline)

    async def get_account_snapshot(self) -> AccountSnapshot:
        return await self.executor.get_account_snapshot()

    async def get_campaign_view(self, campaign: Campaign | None) -> CampaignView | None:
        if campaign is None:
            return None

        orders = await self._get_orders(campaign)

        return CampaignView(
            state=campaign.state,
            health=campaign.health,
            orders=orders,
        )

    async def place_orders(self, order_requests: list[OrderRequest]) -> list[Order]:
        orders: list[Order] = []

        for order_request in order_requests:
            order = await self.executor.place_order(order_request=order_request)
            self._validate_placed_order(order)
            orders.append(order)

        return orders

    async def cancel_and_submit_orders(
        self,
        orders: list[Order],
        order_ids_to_cancel: list[str],
        order_requests: list[OrderRequest],
    ) -> tuple[list[Order], list[Order]]:
        canceled_orders = await self._cancel_orders(
            orders=orders,
            order_ids_to_cancel=order_ids_to_cancel,
        )

        submitted_orders = await self.place_orders(
            order_requests=order_requests,
        )

        return canceled_orders, submitted_orders

    async def _get_orders(self, campaign: Campaign) -> tuple[Order, ...]:
        orders: list[Order] = []

        for order_id in campaign.order_ids:
            order = await self.executor.get_order(order_id)
            orders.append(order)

        return tuple(orders)

    def _validate_placed_order(self, order: Order) -> None:
        if order.order_type == "MARKET":
            if order.status != "FILLED":
                raise MarketOrderNotFullyFilledError(
                    f"Market order #{order.order_id} was not fully filled: "
                    f"status={order.status}"
                )

            return

        if order.order_type == "LIMIT":
            if order.status not in {"NEW", "PARTIALLY_FILLED", "FILLED"}:
                raise UnexpectedOrderStateError(
                    f"Limit order #{order.order_id} returned an unexpected state "
                    f"after placement: status={order.status}"
                )

            return

        raise ValueError(f"Unsupported order type: {order.order_type}")

    async def _cancel_orders(self, orders: list[Order], order_ids_to_cancel: list[str]) -> list[Order]:
        canceled_orders: list[Order] = []

        for order in orders:
            if order.order_id not in order_ids_to_cancel:
                continue

            previous_status = order.status
            canceled_order = await self.executor.cancel_order(order.order_id)

            if canceled_order.filled_quantity != order.filled_quantity:
                raise StrategySignalConflictError(
                    f"Order #{order.order_id} execution changed while applying the strategy signal: "
                    f"status {order.status} -> {canceled_order.status}, "
                    f"filled quantity {order.filled_quantity} -> {canceled_order.filled_quantity}"
                )

            if canceled_order.status != "CANCELED":
                raise OrderCancellationNotCompletedError(
                    f"Order #{order.order_id} was not canceled: "
                    f"status={canceled_order.status}"
                )

            if previous_status != "CANCELED" and canceled_order.status == "CANCELED":
                canceled_orders.append(canceled_order)

        return canceled_orders
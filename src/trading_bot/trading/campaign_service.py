from trading_bot.models.campaign import Campaign
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest
from trading_bot.ports.executor import Executor
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.errors import (
    LimitOrderNotAcceptedError,
    MarketOrderNotAcceptedError,
    MarketOrderNotFullyFilledError,
    OrderCancellationNotCompletedError,
    StrategySignalConflictError, UnexpectedOrderStateError,
)


class CampaignService:

    def __init__(self, executor: Executor, logger: TradingDebugLogger) -> None:
        self.executor = executor
        self.logger = logger

    async def get_orders(self, campaign: Campaign) -> tuple[Order, ...]:
        orders: list[Order] = []

        for order_id in campaign.order_ids:
            order = await self.executor.get_order(order_id)
            orders.append(order)

        return tuple(orders)

    async def open(self, campaign: Campaign, order_requests: list[OrderRequest], kline: KlineEvent) -> None:
        orders = await self._place_orders(order_requests=order_requests, kline=kline)
        campaign.order_ids = [order.order_id for order in orders]
        campaign.mark_open()

    async def close(self, campaign: Campaign, order_requests: list[OrderRequest], kline: KlineEvent) -> None:
        campaign.begin_closing()

        orders = await self.get_orders(campaign)

        pending_order_ids = [
            order.order_id
            for order in orders
            if order.status in {"NEW", "PARTIALLY_FILLED"}
        ]

        await self._cancel_orders(orders=list(orders), order_ids_to_cancel=pending_order_ids)
        self.logger.campaign(f"Orders canceled: {len(pending_order_ids)}")

        close_orders = await self._place_orders(order_requests=order_requests, kline=kline)
        campaign.order_ids.extend([order.order_id for order in close_orders])
        self.logger.campaign(f"Close orders placed: {len(close_orders)}")

        campaign.mark_closed()

    async def _place_orders(self, order_requests: list[OrderRequest], kline: KlineEvent) -> list[Order]:
        orders: list[Order] = []

        for order_request in order_requests:
            order = await self.executor.place_order(order_request=order_request)
            self._validate_placed_order(order)
            orders.append(order)

        self.logger.placed_orders(orders)

        for order in orders:
            if order.status == "FILLED" and order.request.order_type == "MARKET":
                self.logger.fill_market_order(order, kline)

        return orders

    def _validate_placed_order(self, order: Order) -> None:
        if order.request.order_type == "MARKET":
            if order.status == "REJECTED":
                raise MarketOrderNotAcceptedError(
                    f"Market order #{order.order_id} was not accepted: "
                    f"status={order.status}"
                )

            if order.status != "FILLED":
                raise MarketOrderNotFullyFilledError(
                    f"Market order #{order.order_id} was not fully filled: "
                    f"status={order.status}"
                )

            return

        if order.request.order_type == "LIMIT":
            if order.status == "REJECTED":
                raise LimitOrderNotAcceptedError(
                    f"Limit order #{order.order_id} was not accepted: "
                    f"status={order.status}"
                )

            if order.status not in {"NEW", "PARTIALLY_FILLED", "FILLED"}:
                raise UnexpectedOrderStateError(
                    f"Limit order #{order.order_id} returned an unexpected state "
                    f"after placement: status={order.status}"
                )

            return

        raise ValueError(f"Unsupported order type: {order.request.order_type}")

    async def _cancel_orders(self, orders: list[Order], order_ids_to_cancel: list[str]) -> None:
        canceled_orders: list[Order] = []

        for order in orders:
            if order.order_id not in order_ids_to_cancel:
                continue

            previous_status = order.status
            canceled_order = await self.executor.cancel_order(order)

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

        self.logger.canceled_orders(canceled_orders)
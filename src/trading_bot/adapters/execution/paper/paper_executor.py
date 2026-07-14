from dataclasses import replace
from decimal import Decimal

from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.order import Order, OrderRequest


class PaperExecutor:
    def __init__(self, logger: TradingDebugLogger) -> None:
        self._next_order_id = 1
        self.logger = logger

    async def place_order(self, order_request: OrderRequest, kline: KlineEvent) -> Order:
        order_id = str(self._next_order_id)
        self._next_order_id += 1

        if order_request.quantity <= 0:
            return Order(
                order_id=order_id,
                request=order_request,
                status="REJECTED",
                filled_quantity=Decimal("0.0"),
                average_fill_price=None,
            )

        if order_request.order_type == "MARKET":
            return Order(
                order_id=order_id,
                request=order_request,
                status="FILLED",
                filled_quantity=order_request.quantity,
                average_fill_price=kline.close,
            )

        return Order(
            order_id=order_id,
            request=order_request,
            status="NEW",
            filled_quantity=Decimal("0.0"),
            average_fill_price=None,
        )

    async def cancel_order(self, order: Order) -> Order:
        if order.status in {"NEW", "PARTIALLY_FILLED"}:
            return replace(
                order,
                status="CANCELED"
            )

        return order

    async def sync_order_status(self, order: Order, kline: KlineEvent) -> Order:
        if order.status in {"FILLED", "CANCELED", "REJECTED"}:
            return order

        request = order.request

        if request.order_type != "LIMIT" or request.price is None:
            return order

        buy_filled = request.side == "BUY" and kline.low <= request.price
        sell_filled = request.side == "SELL" and kline.high >= request.price

        if not (buy_filled or sell_filled):
            return order

        updated_order = replace(
            order,
            status="FILLED",
            filled_quantity=request.quantity,
            average_fill_price=request.price,
        )

        self.logger.fill_limit_order(updated_order, kline)

        return updated_order
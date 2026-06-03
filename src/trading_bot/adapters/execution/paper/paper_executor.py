from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import Order, OrderRequest


class PaperExecutor:
    def __init__(self) -> None:
        self._next_order_id = 1

    async def place_order(
        self,
        order_request: OrderRequest,
        kline: KlineEvent,
    ) -> Order:
        order_id = str(self._next_order_id)
        self._next_order_id += 1

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
            filled_quantity=0.0,
            average_fill_price=None,
        )

    async def refresh_orders(
        self,
        orders: list[Order],
        kline: KlineEvent,
    ) -> list[Order]:
        for order in orders:
            if order.status in {"FILLED", "CANCELED", "REJECTED"}:
                continue

            request = order.request

            if request.order_type != "LIMIT":
                continue

            if request.price is None:
                continue

            buy_limit_filled = (
                request.side == "BUY"
                and kline.low <= request.price
            )

            sell_limit_filled = (
                request.side == "SELL"
                and kline.high >= request.price
            )

            if buy_limit_filled or sell_limit_filled:
                order.status = "FILLED"
                order.filled_quantity = request.quantity
                order.average_fill_price = request.price

        return orders
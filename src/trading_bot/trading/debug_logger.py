from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import Order


class TradingDebugLogger:
    INDENT = "    "

    def print(self, tag: str, message: str, indent: int = 0) -> None:
        print(f"{self.INDENT * indent}[{tag:<6}] {message}")

    def blank_line(self) -> None:
        print()

    def candle(self, kline: KlineEvent) -> None:
        if abs(kline.close - kline.open) < 0.0001:
            color = "⚪ DOJI"
        elif kline.close > kline.open:
            color = "🟢 GREEN"
        else:
            color = "🔴 RED"

        price_change_pct = (
            (kline.close - kline.open) / kline.open * 100
            if kline.open != 0
            else 0
        )

        self.blank_line()
        self.print(
            "CANDLE",
            f"{kline.open_time.strftime('%Y-%m-%d %H:%M')} | "
            f"{color} | "
            f"O:{kline.open:.4f} H:{kline.high:.4f} "
            f"L:{kline.low:.4f} C:{kline.close:.4f} | "
            f"Change: {price_change_pct:+.3f}% | "
            f"Vol: {kline.volume:,.0f}",
        )

    def signal(self, signal_name: str) -> None:
        self.print("SIGNAL", signal_name, indent=1)

    def trade(self, message: str) -> None:
        self.print("TRADE", message, indent=1)

    def order(self, message: str) -> None:
        self.print("ORDER", message, indent=2)

    def fill_limit_order(self, order: Order, kline: KlineEvent) -> None:
        request = order.request

        price = (
            f"{order.average_fill_price:.4f}"
            if order.average_fill_price is not None
            else "-"
        )

        self.print(
            "FILL",
            f"{request.side} {request.quantity} @ {price} | "
            f"type=LIMIT | "
            f"kline={kline.open_time.strftime('%H:%M')} | "
            f"high={kline.high:.4f} | "
            f"low={kline.low:.4f}",
            indent=1,
        )

    def trade_orders(self, orders: list[Order]) -> None:
        self.trade("Orders:")

        for order in orders:
            price = (
                f"{order.request.price:.4f}"
                if order.request.price is not None
                else "-"
            )

            average_fill_price = (
                f"{order.average_fill_price:.4f}"
                if order.average_fill_price is not None
                else "-"
            )

            self.order(
                f"#{order.order_id} | "
                f"{order.request.side} {order.request.order_type} | "
                f"qty={order.request.quantity} | "
                f"price={price} | "
                f"status={order.status} | "
                f"filled={order.filled_quantity} | "
                f"avg_fill={average_fill_price}"
            )
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import Order, OrderRequest
from trading_bot.trading.campaign import Campaign


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

    def campaign(self, message: str) -> None:
        self.print("CAMPAIGN", message, indent=1)

    def order(self, message: str) -> None:
        self.print("ORDER", message, indent=2)

    def fill(self, message: str) -> None:
        self.print("FILL", message, indent=3)

    def place_order(self, order_id: str, order_request: OrderRequest) -> None:
        price = (
            f"{order_request.price:.4f}"
            if order_request.price is not None
            else "-"
        )

        self.order(
            f"Placing order #{order_id}: "
            f"{order_request.side} {order_request.order_type} | "
            f"qty={order_request.quantity} | "
            f"price={price}"
        )

    def cancel_order(self, order: Order) -> None:
        self.order(
            f"Canceled order #{order.order_id}: "
            f"{order.request.side} {order.request.order_type}"
        )

    def fill_market_order(self, order: Order, kline: KlineEvent) -> None:
        price = (
            f"{order.average_fill_price:.4f}"
            if order.average_fill_price is not None
            else "-"
        )

        self.fill(
            f"Market order filled: "
            f"#{order.order_id} | "
            f"{order.request.side} {order.filled_quantity} @ {price} | "
            f"kline={kline.open_time.strftime('%H:%M')}"
        )

    def fill_limit_order(self, order: Order, kline: KlineEvent) -> None:
        price = (
            f"{order.average_fill_price:.4f}"
            if order.average_fill_price is not None
            else "-"
        )

        self.fill(
            f"Limit order filled: "
            f"#{order.order_id} | "
            f"{order.request.side} {order.filled_quantity} @ {price} | "
            f"kline={kline.open_time.strftime('%H:%M')} | "
            f"high={kline.high:.4f} | "
            f"low={kline.low:.4f}"
        )

    def campaign_summary(self, campaign: Campaign) -> None:
        filled = len([order for order in campaign.orders if order.status == "FILLED"])
        canceled = len([order for order in campaign.orders if order.status == "CANCELED"])
        rejected = len([order for order in campaign.orders if order.status == "REJECTED"])
        active = len([
            order
            for order in campaign.orders
            if order.status not in {"FILLED", "CANCELED", "REJECTED"}
        ])

        status = "ACTIVE" if campaign.is_active else "INACTIVE"
        summary = campaign.execution_summary()

        average_buy_price = (
            f"{summary.average_buy_price:.4f}"
            if summary.average_buy_price is not None
            else "-"
        )

        average_sell_price = (
            f"{summary.average_sell_price:.4f}"
            if summary.average_sell_price is not None
            else "-"
        )

        self.campaign(
            f"{status} | "
            f"orders={len(campaign.orders)} | "
            f"filled={filled} | "
            f"active={active} | "
            f"canceled={canceled} | "
            f"rejected={rejected}"
        )

        self.campaign(
            f"Execution | "
            f"base_delta={summary.net_base_delta:+.8f} | "
            f"quote_delta={summary.net_quote_delta:+.2f} | "
            f"bought={summary.bought_base:.8f} | "
            f"sold={summary.sold_base:.8f}"
        )

        self.campaign(
            f"Average prices | "
            f"buy={average_buy_price} | "
            f"sell={average_sell_price}"
        )

    def campaign_history(self, campaigns: list[Campaign]) -> None:
        open_count = len([campaign for campaign in campaigns if campaign.is_active])
        closed_count = len(campaigns) - open_count

        self.campaign(
            f"History | total={len(campaigns)} | "
            f"open={open_count} | closed={closed_count}"
        )

        for index, campaign in enumerate(campaigns[-5:], start=max(1, len(campaigns) - 4)):
            status = "OPEN" if campaign.is_active else "CLOSED"
            filled = len([order for order in campaign.orders if order.status == "FILLED"])

            self.campaign(
                f"#{index} | "
                f"{status} | "
                f"orders={len(campaign.orders)} | "
                f"filled={filled}"
            )

    def campaign_orders(self, orders: list[Order]) -> None:
        self.campaign("Orders:")

        for order in orders:
            price = (
                f"{order.request.price:.4f}"
                if order.request.price is not None
                else (
                    f"{order.average_fill_price:.4f}"
                    if order.average_fill_price is not None
                    else "-"
                )
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
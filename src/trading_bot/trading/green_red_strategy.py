from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import OrderRequest
from trading_bot.trading.signal import (
    CloseTrade,
    ModifyTrade,
    NoAction,
    OpenTrade,
    StrategySignal,
)
from trading_bot.trading.trade import Trade


class GreenRedStrategy:
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_trade: Trade | None,
    ) -> StrategySignal:
        if current_trade is None:
            if kline.close > kline.open:
                return OpenTrade(
                    order_requests=[
                        OrderRequest(
                            side="BUY",
                            order_type="LIMIT",
                            quantity=1.0,
                            price=kline.close * 0.99,
                        ),
                        OrderRequest(
                            side="BUY",
                            order_type="LIMIT",
                            quantity=1.0,
                            price=kline.close * 0.98,
                        ),
                    ]
                )

            return NoAction()

        if kline.close > kline.open:
            open_order_ids = [
                order.order_id
                for order in current_trade.orders
                if order.status in {"NEW", "PARTIALLY_FILLED"}
            ]

            return ModifyTrade(
                order_ids_to_cancel=open_order_ids,
                order_requests=[
                    OrderRequest(
                        side="BUY",
                        order_type="LIMIT",
                        quantity=1.0,
                        price=kline.close * 0.97,
                    )
                ],
            )

        if kline.close < kline.open:
            open_order_ids = [
                order.order_id
                for order in current_trade.orders
                if order.status in {"NEW", "PARTIALLY_FILLED"}
            ]

            return CloseTrade(
                order_ids_to_cancel=open_order_ids,
                order_requests=[
                    OrderRequest(
                        side="SELL",
                        order_type="MARKET",
                        quantity=1.0,
                    )
                ],
            )

        return NoAction()
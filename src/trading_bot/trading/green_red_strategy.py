from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import OrderRequest
from trading_bot.trading.signal import StrategyAction
from trading_bot.trading.trade import Trade


class GreenRedStrategy:
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_trade: Trade | None,
    ) -> StrategyAction:
        if current_trade is None and kline.close > kline.open:
            return StrategyAction(
                reason="Green candle and no current trade",
                order_requests=[
                    OrderRequest(
                        side="BUY",
                        order_type="MARKET",
                        quantity=1.0,
                    )
                ],
            )

        if current_trade is not None and kline.close < kline.open:
            quantity_to_sell = current_trade.net_quantity

            if quantity_to_sell > 0:
                return StrategyAction(
                    reason="Red candle and current trade exists",
                    order_requests=[
                        OrderRequest(
                            side="SELL",
                            order_type="MARKET",
                            quantity=quantity_to_sell,
                        )
                    ],
                )

        return StrategyAction(
            reason="No action",
            order_requests=[],
        )
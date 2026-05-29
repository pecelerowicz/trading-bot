from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import OrderRequest
from trading_bot.trading.signal import ExitTrade, StartTrade, StrategyResult
from trading_bot.trading.trade import Trade


class GreenRedStrategy:
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_trade: Trade | None,
    ) -> StrategyResult:
        if current_trade is None and kline.close > kline.open:
            return StartTrade(
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
            return ExitTrade(
                reason="Red candle and current trade exists",
            )

        return None

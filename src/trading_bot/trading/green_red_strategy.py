from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.position_state import PositionState
from trading_bot.trading.trading_decision import TradingDecision


class GreenRedStrategy:
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        position: PositionState,
    ) -> TradingDecision:
        if not position.is_open and kline.close > kline.open:
            return TradingDecision(
                action="BUY",
                quantity=1.0,
                reason="Green candle and no open position",
            )

        if position.is_open and kline.close < kline.open:
            return TradingDecision(
                action="SELL",
                quantity=position.quantity,
                reason="Red candle and open position",
            )

        return TradingDecision(
            action="HOLD",
            reason="No action",
        )
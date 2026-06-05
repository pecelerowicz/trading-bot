from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import OrderRequest
from trading_bot.trading.signal import CloseTrade, NoAction, OpenTrade, StrategySignal
from trading_bot.trading.trade import Trade


class GreenRedStrategy:
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_trade: Trade | None,
    ) -> StrategySignal:
        has_no_trade = current_trade is None
        has_trade = current_trade is not None

        is_green_candle = kline.close > kline.open
        is_red_candle = kline.close < kline.open

        if has_no_trade and is_green_candle:
            entry_order_requests = [
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

            return OpenTrade(
                order_requests=entry_order_requests,
            )

        if has_no_trade and not is_green_candle:
            return NoAction()

        if has_trade and is_red_candle:
            open_order_ids = [
                order.order_id
                for order in current_trade.orders
                if order.status in {"NEW", "PARTIALLY_FILLED"}
            ]

            exit_order_requests = [
                OrderRequest(
                    side="SELL",
                    order_type="MARKET",
                    quantity=1.0,
                )
            ]

            return CloseTrade(
                order_ids_to_cancel=open_order_ids,
                order_requests=exit_order_requests,
            )

        if has_trade and not is_red_candle:
            return NoAction()

        return NoAction()
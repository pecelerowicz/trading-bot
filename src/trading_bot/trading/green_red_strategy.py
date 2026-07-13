from decimal import Decimal

from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import OrderRequest
from trading_bot.trading.signal import CloseCampaign, NoAction, OpenCampaign, StrategySignal
from trading_bot.trading.campaign import Campaign


class GreenRedStrategy:
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign: Campaign | None,
    ) -> StrategySignal:
        has_no_campaign = current_campaign is None
        has_campaign = current_campaign is not None

        is_green_candle = kline.close > kline.open
        is_red_candle = kline.close < kline.open

        if has_no_campaign and is_green_candle:
            entry_order_requests = [
                OrderRequest(
                    side="BUY",
                    order_type="LIMIT",
                    quantity=Decimal("1.0"),
                    price=kline.close * Decimal("0.99"),
                ),
                OrderRequest(
                    side="BUY",
                    order_type="LIMIT",
                    quantity=Decimal("1.0"),
                    price=kline.close * Decimal("0.98"),
                ),
            ]

            return OpenCampaign(
                order_requests=entry_order_requests,
            )

        if has_no_campaign and not is_green_candle:
            return NoAction()

        if has_campaign and is_red_candle:
            open_order_ids = [
                order.order_id
                for order in current_campaign.orders
                if order.status in {"NEW", "PARTIALLY_FILLED"}
            ]

            exit_order_requests = [
                OrderRequest(
                    side="SELL",
                    order_type="MARKET",
                    quantity=Decimal("1.0"),
                )
            ]

            return CloseCampaign(
                order_ids_to_cancel=open_order_ids,
                order_requests=exit_order_requests,
            )

        if has_campaign and not is_red_candle:
            return NoAction()

        return NoAction()
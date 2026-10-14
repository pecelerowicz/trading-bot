from decimal import Decimal

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import CampaignView
from trading_bot.models.instrument import Instrument
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import OrderRequest
from trading_bot.trading.signal import StrategySignal


class ThreeGreenPyramidSellStrategy:

    def __init__(self, instrument: Instrument) -> None:
        self.instrument = instrument

    def create_signal(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign_view: CampaignView | None,
        account_snapshot: AccountSnapshot,
    ) -> StrategySignal:
        if current_campaign_view is None:
            return self._on_no_campaign(
                kline=kline,
                klines=klines,
                account_snapshot=account_snapshot,
            )

        if current_campaign_view.is_open:
            return self._on_open_campaign(
                kline=kline,
                klines=klines,
                current_campaign=current_campaign_view,
                account_snapshot=account_snapshot,
            )

        raise RuntimeError(
            f"Campaign in unexpected state: {current_campaign_view.state.value}"
        )

    def _on_no_campaign(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        account_snapshot: AccountSnapshot,
    ) -> StrategySignal:
        if len(klines) < 3:
            return StrategySignal.idle()

        last_three = klines[-3:]
        is_three_consecutive_green = all(
            candle.close > candle.open for candle in last_three
        )

        if not is_three_consecutive_green:
            return StrategySignal.idle()

        current_close = kline.close
        order_requests: list[OrderRequest] = []

        for i in range(10):
            price = current_close * (1 + i * Decimal("0.0002"))
            order_requests.append(
                OrderRequest(
                    side="SELL",
                    order_type="LIMIT",
                    quantity=Decimal("0.1"),
                    price=round(price, 2),
                )
            )

        required_base = sum(
            (
                order_request.quantity
                for order_request in order_requests
            ),
            Decimal("0"),
        )

        if not account_snapshot.has_free_balance(
            self.instrument.base_asset,
            required_base,
        ):
            return StrategySignal.idle()

        return StrategySignal.open_campaign(
            order_requests=order_requests,
        )

    def _on_open_campaign(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign: CampaignView,
        account_snapshot: AccountSnapshot,
    ) -> StrategySignal:
        if len(klines) >= 2:
            last_two = klines[-2:]
            is_two_consecutive_red = all(
                candle.close < candle.open for candle in last_two
            )

            if is_two_consecutive_red:
                summary = current_campaign.execution_summary()

                quantity_to_buy_back = summary.sold_base - summary.bought_base
                quantity_to_buy_back = max(
                    quantity_to_buy_back,
                    Decimal("0.0"),
                )

                order_requests: list[OrderRequest] = []

                if quantity_to_buy_back > Decimal("0"):
                    required_quote = quantity_to_buy_back * kline.close

                    if not account_snapshot.has_free_balance(
                        self.instrument.quote_asset,
                        required_quote,
                    ):
                        return StrategySignal.hold_campaign()

                    order_requests.append(
                        OrderRequest(
                            side="BUY",
                            order_type="MARKET",
                            quantity=quantity_to_buy_back,
                        )
                    )

                cancel_order_ids = [
                    order.order_id
                    for order in current_campaign.orders
                    if order.status in {"NEW", "PARTIALLY_FILLED"}
                ]

                return StrategySignal.close_campaign(
                    cancel_order_ids=cancel_order_ids,
                    order_requests=order_requests,
                )

        return StrategySignal.hold_campaign()
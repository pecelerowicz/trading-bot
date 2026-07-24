from decimal import Decimal

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.instrument import Instrument
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import OrderRequest
from trading_bot.trading.signal import OpenCampaign, CloseCampaign, NoAction, StrategySignal
from trading_bot.trading.campaign import Campaign


class ThreeGreenPyramidSellStrategy:

    def __init__(self, instrument: Instrument) -> None:
        self.instrument = instrument

    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign: Campaign | None,
        account_snapshot: AccountSnapshot
    ) -> StrategySignal:

        # === CLOSING LOGIC ===
        if current_campaign is not None:
            if len(klines) >= 2:
                last_two = klines[-2:]
                is_two_consecutive_red = all(
                    candle.close < candle.open for candle in last_two
                )

                if is_two_consecutive_red:
                    summary = current_campaign.execution_summary()

                    quantity_to_buy_back = summary.sold_base - summary.bought_base
                    quantity_to_buy_back = max(quantity_to_buy_back, Decimal("0.0"))

                    order_requests: list[OrderRequest] = []

                    if quantity_to_buy_back > Decimal("0"):
                        required_quote = quantity_to_buy_back * kline.close

                        if not account_snapshot.has_free_balance(self.instrument.quote_asset, required_quote):
                            return NoAction()

                        order_requests.append(
                            OrderRequest(
                                side="BUY",
                                order_type="MARKET",
                                quantity=quantity_to_buy_back,
                            )
                        )

                    return CloseCampaign(
                        order_requests=order_requests,
                        order_ids_to_cancel=[
                            order_id
                            for order_id in current_campaign.order_ids
                            if (
                                order := current_campaign.get_order(order_id)
                            ) is not None
                            and order.status in {"NEW", "PARTIALLY_FILLED"}
                        ],
                    )

            return NoAction()

        # === OPENING LOGIC ===
        if len(klines) < 3:
            return NoAction()

        last_three = klines[-3:]
        is_three_consecutive_green = all(
            candle.close > candle.open for candle in last_three
        )

        if not is_three_consecutive_green:
            return NoAction()

        current_close = kline.close
        order_requests: list[OrderRequest] = []

        for i in range(10):
            price = current_close * (1 + i * Decimal("0.0002"))
            order_requests.append(
                OrderRequest(
                    side="SELL",
                    order_type="LIMIT",
                    quantity=Decimal("1.0"),
                    price=round(price, 2),
                )
            )

        required_base = sum(
            (
                order_request.quantity
                for order_request in order_requests
            ),
            Decimal("0")
        )

        if not account_snapshot.has_free_balance(self.instrument.base_asset, required_base):
            return NoAction()

        return OpenCampaign(order_requests=order_requests)
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import OrderRequest
from trading_bot.trading.signal import OpenCampaign, CloseCampaign, NoAction, StrategySignal
from trading_bot.trading.campaign import Campaign


class ThreeGreenPyramidSellStrategy:
    """
    Short strategy with the following rules:

    Entry:  Open short position after 3 consecutive green candles
            → Places 4 limit sell orders in a pyramid (+0%, +1%, +2%, +3%)

    Exit:   Close position after 2 consecutive red candles
            → Market buy to close + cancel remaining limit orders
    """

    def on_kline(
            self,
            kline: KlineEvent,
            klines: list[KlineEvent],
            current_campaign: Campaign | None,
    ) -> StrategySignal:

        # === CLOSING LOGIC ===
        if current_campaign is not None:
            if len(klines) >= 2:
                last_two = klines[-2:]
                is_two_consecutive_red = all(
                    candle.close < candle.open for candle in last_two
                )

                if is_two_consecutive_red:
                    return CloseCampaign(
                        order_requests=[
                            OrderRequest(
                                side="BUY",  # BUY to close short
                                order_type="MARKET",
                                quantity=1.0,
                            )
                        ],
                        order_ids_to_cancel=[
                            order.order_id
                            for order in current_campaign.orders
                            if order.status in {"NEW", "PARTIALLY_FILLED"}
                        ]
                    )

            return NoAction()

        # === OPENING LOGIC ===
        if len(klines) < 3:
            return NoAction()

        # Check last 3 candles
        last_three = klines[-3:]
        is_three_consecutive_green = all(
            candle.close > candle.open for candle in last_three
        )

        if not is_three_consecutive_green:
            return NoAction()

        # Build pyramid sell orders
        current_close = kline.close
        order_requests: list[OrderRequest] = []

        for i in range(10):
            price = current_close * (1 + i * 0.0002)
            order_requests.append(
                OrderRequest(
                    side="SELL",
                    order_type="LIMIT",
                    quantity=1.0,
                    price=round(price, 2),
                )
            )

        return OpenCampaign(order_requests=order_requests)
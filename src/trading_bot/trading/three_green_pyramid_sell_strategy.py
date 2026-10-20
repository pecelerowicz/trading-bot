from decimal import Decimal

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import OrderStateSnapshot
from trading_bot.models.instrument import Instrument
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import OrderRequest
from trading_bot.models.step_record import StepRecord
from trading_bot.trading.signal import SignalType, StrategySignal


class ThreeGreenPyramidSellStrategy:

    def __init__(self, instrument: Instrument) -> None:
        self.instrument = instrument

    def create_signal(self, kline: KlineEvent, klines: list[KlineEvent], account_snapshot: AccountSnapshot,
                      order_state_snapshot: OrderStateSnapshot, step_records: list[StepRecord]) -> StrategySignal:
        if self._is_active(step_records):
            return self._on_active_campaign(kline=kline, klines=klines, order_state_snapshot=order_state_snapshot,
                                            account_snapshot=account_snapshot)

        return self._on_inactive_campaign(kline=kline, klines=klines, account_snapshot=account_snapshot)

    def _is_active(self, step_records: list[StepRecord]) -> bool:
        if not step_records:
            return False

        return step_records[-1].signal.signal_type in {
            SignalType.OPEN,
            SignalType.HOLD,
        }

    def _on_active_campaign(self, kline: KlineEvent, klines: list[KlineEvent], order_state_snapshot: OrderStateSnapshot,
                            account_snapshot: AccountSnapshot) -> StrategySignal:
        if len(klines) >= 2:
            last_two = klines[-2:]
            is_two_consecutive_red = all(candle.close < candle.open for candle in last_two)

            if is_two_consecutive_red:
                summary = order_state_snapshot.fill_summary()

                quantity_to_buy_back = summary.sold_base - summary.bought_base
                quantity_to_buy_back = max(quantity_to_buy_back, Decimal("0.0"))

                order_requests: list[OrderRequest] = []

                if quantity_to_buy_back > Decimal("0"):
                    required_quote = quantity_to_buy_back * kline.close

                    if not account_snapshot.has_free_balance(self.instrument.quote_asset, required_quote):
                        return StrategySignal.hold_campaign()

                    order_requests.append(OrderRequest(side="BUY", order_type="MARKET", quantity=quantity_to_buy_back))

                cancel_order_ids = [order.order_id for order in order_state_snapshot.orders
                                    if order.status in {"NEW", "PARTIALLY_FILLED"}]

                return StrategySignal.close_campaign(cancel_order_ids=cancel_order_ids, order_requests=order_requests)

        return StrategySignal.hold_campaign()

    def _on_inactive_campaign(self, kline: KlineEvent, klines: list[KlineEvent],
                              account_snapshot: AccountSnapshot) -> StrategySignal:
        if len(klines) < 3:
            return StrategySignal.idle()

        last_three = klines[-3:]
        is_three_consecutive_green = all(candle.close > candle.open for candle in last_three)

        if not is_three_consecutive_green:
            return StrategySignal.idle()

        current_close = kline.close
        order_requests: list[OrderRequest] = []

        for i in range(10):
            price = current_close * (1 + i * Decimal("0.0002"))
            order_requests.append(
                OrderRequest(side="SELL", order_type="LIMIT", quantity=Decimal("0.1"), price=round(price, 2)))

        required_base = sum(
            (
                order_request.quantity
                for order_request in order_requests
            ),
            Decimal("0"),
        )

        if not account_snapshot.has_free_balance(self.instrument.base_asset, required_base):
            return StrategySignal.idle()

        return StrategySignal.open_campaign(order_requests=order_requests)
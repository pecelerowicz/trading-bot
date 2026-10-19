from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import OrderStateSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.step_record import StepRecord
from trading_bot.trading.signal import StrategySignal


class Strategy(Protocol):
    def create_signal(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        order_state_snapshot: OrderStateSnapshot | None,
        account_snapshot: AccountSnapshot,
    ) -> StrategySignal:
        ...

    def create_signal2(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        account_snapshot: AccountSnapshot,
        step_records: list[StepRecord],
    ) -> StrategySignal:
        ...
from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.order_state import OrderStateSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.step_record import KlineRecord
from trading_bot.trading.signal import StrategySignal


class Strategy(Protocol):
    def create_signal(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        account_snapshot: AccountSnapshot,
        order_state_snapshot: OrderStateSnapshot,
        step_records: list[KlineRecord],
    ) -> StrategySignal:
        ...
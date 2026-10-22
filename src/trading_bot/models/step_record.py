from dataclasses import dataclass

from trading_bot.models.order_state import OrderStateSnapshot
from trading_bot.models.execution import Execution
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.signal import StrategySignal


@dataclass(frozen=True)
class KlineRecord:
    kline: KlineEvent
    order_state_snapshot: OrderStateSnapshot
    signal: StrategySignal
    execution: Execution
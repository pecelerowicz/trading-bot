from dataclasses import dataclass

from trading_bot.models.execution import Execution
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.signal import StrategySignal


@dataclass(frozen=True)
class StepRecord:
    kline: KlineEvent
    signal: StrategySignal
    execution: Execution
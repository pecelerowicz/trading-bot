from dataclasses import dataclass
from typing import Literal


Action = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class TradingDecision:
    action: Action
    quantity: float = 0.0
    reason: str = ""
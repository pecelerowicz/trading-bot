from dataclasses import dataclass
from datetime import datetime


@dataclass
class KlineEvent:
    event_time: datetime | None
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool

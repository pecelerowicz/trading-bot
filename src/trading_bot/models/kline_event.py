from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class KlineEvent:
    event_time: datetime | None
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_closed: bool

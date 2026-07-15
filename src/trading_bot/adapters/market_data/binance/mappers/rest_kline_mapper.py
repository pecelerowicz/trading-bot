from decimal import Decimal

import pandas as pd
from trading_bot.models.kline_event import KlineEvent

def map_rest_kline(bar: list) -> KlineEvent:
    return KlineEvent(
        event_time=None,
        open_time=pd.to_datetime(bar[0], unit="ms", utc=True).to_pydatetime(),
        open=Decimal(bar[1]),
        high=Decimal(bar[2]),
        low=Decimal(bar[3]),
        close=Decimal(bar[4]),
        volume=Decimal(bar[5]),
        is_closed=True,
    )

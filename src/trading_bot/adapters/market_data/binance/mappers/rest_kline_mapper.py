import pandas as pd
from trading_bot.models.kline_event import KlineEvent

def map_rest_kline(bar: list) -> KlineEvent:
    return KlineEvent(
        event_time=None,
        open_time=pd.to_datetime(bar[0], unit="ms", utc=True).to_pydatetime(),
        open=float(bar[1]),
        high=float(bar[2]),
        low=float(bar[3]),
        close=float(bar[4]),
        volume=float(bar[5]),
        is_closed=True,
    )

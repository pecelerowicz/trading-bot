from datetime import datetime, timezone
from decimal import Decimal

from trading_bot.models.kline_event import KlineEvent


def map_ws_kline(msg: dict) -> KlineEvent:
    k = msg["k"]

    return KlineEvent(
        event_time=datetime.fromtimestamp(msg["E"] / 1000, tz=timezone.utc),
        open_time=datetime.fromtimestamp(k["t"] / 1000, tz=timezone.utc),
        open=Decimal(k["o"]),
        high=Decimal(k["h"]),
        low=Decimal(k["l"]),
        close=Decimal(k["c"]),
        volume=Decimal(k["v"]),
        is_closed=k["x"],
    )

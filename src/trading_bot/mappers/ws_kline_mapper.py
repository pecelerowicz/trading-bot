from datetime import datetime, timezone
from trading_bot.models.kline_event import KlineEvent


def map_ws_kline(msg: dict) -> KlineEvent:
    k = msg["k"]

    return KlineEvent(
        event_time=datetime.fromtimestamp(msg["E"] / 1000, tz=timezone.utc),
        open_time=datetime.fromtimestamp(k["t"] / 1000, tz=timezone.utc),
        open=float(k["o"]),
        high=float(k["h"]),
        low=float(k["l"]),
        close=float(k["c"]),
        volume=float(k["v"]),
        is_closed=k["x"],
    )

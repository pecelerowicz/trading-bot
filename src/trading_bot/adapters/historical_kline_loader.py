import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from trading_bot.models.kline_event import KlineEvent


def load_historical_klines(
    file_path: str | Path,
    mapper: Callable[[Any], KlineEvent],
    initial_date,
    final_date,
) -> list[KlineEvent]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Local data file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_klines = json.load(f)

    if not isinstance(raw_klines, list):
        raise ValueError(f"Expected list in local data file, got: {type(raw_klines)}")

    initial_datetime = pd.to_datetime(initial_date, utc=True).to_pydatetime()
    final_datetime = pd.to_datetime(final_date, utc=True).to_pydatetime()

    klines = []

    for raw_kline in raw_klines:
        kline = mapper(raw_kline)

        if initial_datetime <= kline.open_time <= final_datetime:
            klines.append(kline)

    return klines
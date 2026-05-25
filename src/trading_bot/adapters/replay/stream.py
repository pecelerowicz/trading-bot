import asyncio
import json
from pathlib import Path

import pandas as pd

from trading_bot.mappers.rest_kline_mapper import map_rest_kline


class LocalMarketDataSource:
    def __init__(
        self,
        symbol: str,
        interval: str,
        initial_date,
        final_date,
        delay_seconds: float,
    ):
        self.symbol = symbol
        self.interval = interval
        self.initial_date = pd.to_datetime(initial_date, utc=True).to_pydatetime()
        self.final_date = pd.to_datetime(final_date, utc=True).to_pydatetime()
        self.delay_seconds = delay_seconds

    async def stream_klines(self):
        raw_klines = self._load_raw_klines()
        filtered_raw_klines = self._filter_raw_klines(raw_klines)

        for raw_bar in filtered_raw_klines:
            kline = map_rest_kline(raw_bar)

            await asyncio.sleep(self.delay_seconds)

            yield kline

    def _data_file_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[4]
        return project_root / "data" / f"{self.symbol}_{self.interval}.json"

    def _load_raw_klines(self) -> list[list]:
        file_path = self._data_file_path()

        if not file_path.exists():
            raise FileNotFoundError(f"Local data file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(f"Expected list in local data file, got: {type(data)}")

        return data

    def _filter_raw_klines(self, raw_klines: list[list]) -> list[list]:
        filtered = []

        for bar in raw_klines:
            open_time = pd.to_datetime(bar[0], unit="ms", utc=True).to_pydatetime()

            if self.initial_date <= open_time <= self.final_date:
                filtered.append(bar)

        return filtered
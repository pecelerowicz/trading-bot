import asyncio
import json
from pathlib import Path

import pandas as pd
from binance import AsyncClient, BinanceSocketManager

from trading_bot.mappers.rest_kline_mapper import map_rest_kline
from trading_bot.mappers.ws_kline_mapper import map_ws_kline
from trading_bot.trading.trading_session import TradingSession


class BinanceMarketDataSource:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool,
        symbol: str,
        interval: str,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.symbol = symbol
        self.interval = interval

    async def stream_klines(self):
        async_client = await AsyncClient.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=self.testnet,
        )

        try:
            bm = BinanceSocketManager(async_client)
            ts = bm.kline_socket(
                symbol=self.symbol,
                interval=self.interval,
            )

            async with ts as stream:
                while True:
                    raw_msg = await stream.recv()
                    yield map_ws_kline(raw_msg)

        finally:
            await async_client.close_connection()


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
        project_root = Path(__file__).resolve().parents[3]
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


class TradingApp:
    def __init__(
        self,
        market_data_source,
        trading_session: TradingSession,
    ):
        self.market_data_source = market_data_source
        self.trading_session = trading_session

    async def run(self):
        async for kline in self.market_data_source.stream_klines():
            should_stop = await self.trading_session.handle_kline(kline)

            if should_stop:
                break
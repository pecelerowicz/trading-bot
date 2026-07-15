from collections.abc import AsyncIterator
from typing import Protocol

from trading_bot.models.kline_event import KlineEvent


class MarketDataSource(Protocol):
    def stream_klines(self) -> AsyncIterator[KlineEvent]:
        ...
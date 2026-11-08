import asyncio

from trading_bot.models.kline_event import KlineEvent


class ReplayMarketDataSource:
    def __init__(
        self,
        klines: list[KlineEvent],
        delay_seconds: float,
    ):
        self.klines = klines
        self.delay_seconds = delay_seconds

    async def stream_klines(self):
        for kline in self.klines:
            await asyncio.sleep(self.delay_seconds)

            yield kline
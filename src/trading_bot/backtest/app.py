from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.trading_session import TradingSession


class BacktestApp:
    def __init__(
        self,
        klines: list[KlineEvent],
        trading_session: TradingSession,
    ):
        self.klines = klines
        self.trading_session = trading_session

    async def run(self) -> None:
        for kline in self.klines:
            await self.trading_session.handle_kline(kline)
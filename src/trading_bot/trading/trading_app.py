from trading_bot.trading.trading_session import TradingSession


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
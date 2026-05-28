from trading_bot.models.kline_event import KlineEvent


class TradingSession:
    def __init__(self, strategy, executor) -> None:
        self.strategy = strategy
        self.executor = executor
        self.klines: list[KlineEvent] = []

    async def handle_kline(self, kline: KlineEvent) -> bool:
        if not kline.is_closed:
            return False

        self.klines.append(kline)

        return False




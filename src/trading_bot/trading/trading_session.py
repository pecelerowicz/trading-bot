from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.signal import StartTrade
from trading_bot.trading.trade import Trade


class TradingSession:
    def __init__(self, strategy, executor) -> None:
        self.strategy = strategy
        self.executor = executor
        self.klines: list[KlineEvent] = []
        self.current_trade: Trade | None = None

    async def handle_kline(self, kline: KlineEvent) -> bool:
        if not kline.is_closed:
            return False

        self.klines.append(kline)

        result = self.strategy.on_kline(
            kline=kline,
            klines=self.klines,
            current_trade=self.current_trade,
        )

        print(result)

        if isinstance(result, StartTrade):
            self._start_trade(result)

        return False

    def _start_trade(self, signal: StartTrade) -> None:
        if self.current_trade is not None:
            return

        self.current_trade = Trade(
            reason=signal.reason,
            orders=[],
        )

        print(f"Trade started: {self.current_trade.reason}")
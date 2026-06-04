from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.signal import CloseTrade, ModifyTrade, NoAction, OpenTrade
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

        # TODO: In the future, executor will refresh current trade orders here.

        signal = self.strategy.on_kline(
            kline=kline,
            klines=self.klines,
            current_trade=self.current_trade,
        )

        print(signal)

        if isinstance(signal, OpenTrade):
            self._open_trade(signal)
            return False

        if isinstance(signal, ModifyTrade):
            self._modify_trade(signal)
            return False

        if isinstance(signal, CloseTrade):
            self._close_trade(signal)
            return False

        if isinstance(signal, NoAction):
            return False

        return False

    def _open_trade(self, signal: OpenTrade) -> None:
        if self.current_trade is not None:
            print("OpenTrade ignored: current trade already exists")
            return

        self.current_trade = Trade(
            orders=[],
            is_open=True,
        )

        print(f"Trade opened with {len(signal.order_requests)} requested orders")

    def _modify_trade(self, signal: ModifyTrade) -> None:
        if self.current_trade is None:
            print("ModifyTrade ignored: no current trade")
            return

        print(
            f"Trade modification requested: "
            f"{len(signal.order_requests)} new orders, "
            f"{len(signal.order_ids_to_cancel)} orders to cancel"
        )

    def _close_trade(self, signal: CloseTrade) -> None:
        if self.current_trade is None:
            print("CloseTrade ignored: no current trade")
            return

        self.current_trade.is_open = False
        self.current_trade = None

        print(
            f"Trade closed with {len(signal.order_requests)} requested close orders "
            f"and {len(signal.order_ids_to_cancel)} orders to cancel"
        )
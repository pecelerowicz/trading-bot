from trading_bot.trading.paper_executor import ExecutionResult, PaperExecutor
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.position_state import PositionState


class TradingSession:
    def __init__(self, strategy, executor) -> None:
        self.strategy = strategy
        self.executor = executor
        self.klines: list[KlineEvent] = []
        self.position = PositionState()

    async def handle_kline(self, kline: KlineEvent) -> bool:
        if not kline.is_closed:
            return False

        self.klines.append(kline)

        decision = self.strategy.on_kline(kline=kline, klines=self.klines, position=self.position)

        print(f"Strategy decision: {decision.action} | {decision.reason}")

        result = await self.executor.execute(decision=decision, kline=kline)

        if result is not None:
            self._apply_execution_result(result)

        return False

    def _apply_execution_result(self, result: ExecutionResult) -> None:
        if result.action == "BUY":
            self._apply_buy(result)
        elif result.action == "SELL":
            self._apply_sell(result)

    def _apply_buy(self, result: ExecutionResult) -> None:
        self.position.is_open = True
        self.position.entry_price = result.fill_price
        self.position.quantity = result.quantity

        print(
            f"Position opened: quantity={self.position.quantity}, "
            f"entry_price={self.position.entry_price}"
        )

    def _apply_sell(self, result: ExecutionResult) -> None:
        entry_price = self.position.entry_price
        exit_price = result.fill_price
        quantity = self.position.quantity

        pnl = None
        if entry_price is not None:
            pnl = (exit_price - entry_price) * quantity

        print(
            f"Position closed: quantity={quantity}, "
            f"exit_price={exit_price}, pnl={pnl}"
        )

        self.position = PositionState()
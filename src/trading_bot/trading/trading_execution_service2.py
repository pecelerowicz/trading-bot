from trading_bot.errors import (
    MarketOrderNotFullyFilledError,
    OrderCancellationNotCompletedError,
    StrategySignalConflictError, UnexpectedOrderStateError,
)
from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import Campaign, CampaignView
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest
from trading_bot.ports.executor import Executor
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.signal import SignalType, StrategySignal

class Execution:
    pass

class TradingExecutionService2:

    def __init__(self, executor: Executor, logger: TradingDebugLogger) -> None:
        self.executor = executor
        self.logger = logger

    async def update_executor(self, kline: KlineEvent) -> None:
        await self.executor.update_executor(kline)

    async def execute_signal(self, signal: StrategySignal) -> Execution:
        if signal is None:
            self.logger.signal("NoAction")
            return

        cancelled_orders = await self._cancel_orders(cancel_order_ids = signal.cancel_order_ids)
        placed_orders = await self._place_orders(order_requests=signal.order_requests)

    async def _cancel_orders(self, cancel_order_is: list[str]):
        pass

    async def _place_orders(self):

    async def get_signal_execution(self, signal: StrategySignal) -> Execution:
        pass





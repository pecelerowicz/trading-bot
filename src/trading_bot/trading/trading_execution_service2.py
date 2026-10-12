from trading_bot.ports.executor import Executor
from trading_bot.trading.debug_logger import TradingDebugLogger


class TradingExecutionService2:

    def __init__(self, executor: Executor, logger: TradingDebugLogger) -> None:
        self.executor = executor
        self.logger = logger
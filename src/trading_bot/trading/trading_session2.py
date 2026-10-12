from trading_bot.models.campaign import Campaign
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.strategy import Strategy
from trading_bot.trading.trading_execution_service2 import TradingExecutionService2


class TradingSession2:

    def __init__(
        self,
        strategy: Strategy,
        execution_service: TradingExecutionService2,
        logger: TradingDebugLogger,
        reconciliation_reporter: PortfolioReconciliationReporter,
    ) -> None:
        self.strategy = strategy
        self.execution_service = execution_service
        self.logger = logger
        self.reconciliation_reporter = reconciliation_reporter

        self.klines: list[KlineEvent] = []
        self.campaigns: list[Campaign] = []
        self.current_campaign: Campaign | None = None
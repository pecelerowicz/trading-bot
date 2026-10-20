from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.step_record import StepRecord
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.strategy import Strategy
from trading_bot.trading.trading_execution_service import TradingExecutionService


class TradingSession:

    def __init__(
        self,
        strategy: Strategy,
        execution_service: TradingExecutionService,
        logger: TradingDebugLogger,
        reconciliation_reporter: PortfolioReconciliationReporter,
    ) -> None:
        self.strategy = strategy
        self.execution_service = execution_service
        self.logger = logger
        self.reconciliation_reporter = reconciliation_reporter

        self.klines: list[KlineEvent] = []
        self.account_snapshot: AccountSnapshot | None = None
        self.step_records: list[StepRecord] = []

    async def handle_kline(self, kline: KlineEvent) -> None:
        try:
            await self._handle_kline(kline)
        except Exception as error:
            self._require_recovery(error)
            raise

    async def _handle_kline(self, kline: KlineEvent) -> None:
        if not kline.is_closed:
            return
        await self.execution_service.update_executor(kline)

        self.logger.candle(kline)
        self.klines.append(kline)

        self.account_snapshot: AccountSnapshot = await self.execution_service.get_account_snapshot()

        signal = self.strategy.create_signal2(kline, self.klines, self.account_snapshot, self.step_records)
        self.logger.signal(signal.signal_type.value)

        execution = await self.execution_service.execute_signal(signal, kline)
        self.logger.execution(execution, kline)

        self.step_records.append(StepRecord(kline, signal, execution))

    def _require_recovery(self, error: Exception) -> None:
        pass
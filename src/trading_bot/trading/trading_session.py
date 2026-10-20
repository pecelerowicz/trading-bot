from trading_bot.models.account import AccountSnapshot
from trading_bot.models.campaign import OrderStateSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.step_record import KlineRecord
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.signal import SignalType
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
        self.kline_records: list[KlineRecord] = []
        self.account_snapshot: AccountSnapshot | None = None
        self.order_state_snapshot: OrderStateSnapshot | None = None

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
        self.order_state_snapshot: OrderStateSnapshot = await self._get_order_state_snapshot()

        signal = self.strategy.create_signal(kline, self.klines, self.account_snapshot,
                                             self.order_state_snapshot, self.kline_records)
        self.logger.signal(signal.signal_type.value)

        execution = await self.execution_service.execute_signal(signal)
        self.logger.execution(execution, kline)

        self.kline_records.append(KlineRecord(kline, signal, execution))

    async def _get_order_state_snapshot(self) -> OrderStateSnapshot:
        if not self.kline_records:
            return OrderStateSnapshot(orders=())

        if self.kline_records[-1].signal.signal_type not in {SignalType.OPEN, SignalType.HOLD}:
            return OrderStateSnapshot(orders=())

        order_ids: list[str] = []

        for record in reversed(self.kline_records):
            for placement in record.execution.placements:
                if placement.order is not None and placement.order.order_id not in order_ids:
                    order_ids.append(placement.order.order_id)

            if record.signal.signal_type == SignalType.OPEN:
                break
        return await self.execution_service.get_order_state_snapshot(order_ids)

    def _require_recovery(self, error: Exception) -> None:
        pass
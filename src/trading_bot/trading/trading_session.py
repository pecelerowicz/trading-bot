from trading_bot.models.account import AccountSnapshot
from trading_bot.models.order_state import OrderStateSnapshot
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

        self.current_kline: KlineEvent | None = None
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
        self.current_kline = kline
        self.logger.candle(self.current_kline)

        await self.execution_service.update_executor(self.current_kline)

        self.klines.append(self.current_kline)

        self.order_state_snapshot: OrderStateSnapshot = await self._get_order_state_snapshot()
        self._log_order_state_changes()

        self.account_snapshot: AccountSnapshot = await self.execution_service.get_account_snapshot()

        signal = self.strategy.create_signal(self.current_kline, self.klines, self.account_snapshot,
                                             self.order_state_snapshot, self.kline_records)
        self.logger.signal(signal.signal_type.value)

        execution = await self.execution_service.execute_signal(signal)
        self.logger.execution(execution, self.current_kline)

        self.kline_records.append(KlineRecord(self.current_kline, self.order_state_snapshot, signal, execution))

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

    def _log_order_state_changes(self) -> None:
        if not self.kline_records or self.order_state_snapshot is None:
            return

        previous_record = self.kline_records[-1]

        previous_orders = {order.order_id: order for order in previous_record.order_state_snapshot.orders}

        for cancellation in previous_record.execution.cancellations:
            if cancellation.order is not None:
                previous_orders[cancellation.order.order_id] = cancellation.order

        for placement in previous_record.execution.placements:
            if placement.order is not None:
                previous_orders[placement.order.order_id] = placement.order

        for order in self.order_state_snapshot.orders:
            previous_order = previous_orders.get(order.order_id)

            if previous_order is None:
                continue

            if previous_order.status != order.status or previous_order.filled_quantity != order.filled_quantity:
                self.logger.order(
                    f"Order #{order.order_id} changed: "
                    f"status {previous_order.status} -> {order.status}, "
                    f"filled {previous_order.filled_quantity} -> {order.filled_quantity}"
                )

    def _require_recovery(self, error: Exception) -> None:
        pass
from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.campaign import Campaign, CampaignView
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.signal import SignalType, StrategySignal
from trading_bot.trading.strategy import Strategy
from trading_bot.trading.trading_execution_service import TradingExecutionService


class TradingSession:

    def __init__(self, strategy: Strategy, execution_service: TradingExecutionService, logger: TradingDebugLogger, reconciliation_reporter: PortfolioReconciliationReporter) -> None:
        self.strategy = strategy
        self.execution_service = execution_service
        self.logger = logger
        self.reconciliation_reporter = reconciliation_reporter
        self.kline: KlineEvent | None = None
        self.klines: list[KlineEvent] = []
        self.campaigns: list[Campaign] = []
        self.current_campaign: Campaign | None = None
        self.current_campaign_view: CampaignView | None = None
        self.account_snapshot: AccountSnapshot | None = None

    async def handle_kline(self, kline: KlineEvent) -> None:
        try:
            await self._handle_kline(kline)
        except Exception as error:
            self._require_recovery(error)
            raise

    async def _handle_kline(self, kline: KlineEvent) -> None:

        # preliminary work
        if not kline.is_closed:
            return
        self.logger.candle(kline)
        await self.execution_service.update_executor(kline)

        # current world
        self.kline = kline
        self.klines.append(kline)
        self.current_campaign_view = await self.execution_service.get_campaign_view(self.current_campaign)
        self.account_snapshot = await self.execution_service.get_account_snapshot()

        # actual processing
        signal = self.strategy.on_kline(self.kline, self.klines, self.current_campaign_view, self.account_snapshot)
        execution = await self._execute_strategy_signal(signal, kline)

    async def _execute_strategy_signal(self, signal: StrategySignal | None, kline: KlineEvent) -> None:
        if signal is None:
            self.logger.signal("NoAction")
            return

        self.logger.signal(signal.signal_type.value)

        match signal.signal_type:
            case SignalType.OPEN:
                await self._open_campaign(signal, kline)

            case SignalType.CLOSE:
                await self._close_campaign(signal, kline)

            case _:
                raise TypeError(f"Unsupported strategy signal type: {signal.signal_type}")

    async def _open_campaign(self, signal: StrategySignal, kline: KlineEvent) -> None:
        if self.current_campaign is not None:
            self.logger.campaign("Open signal ignored: current campaign already exists")
            return

        campaign = Campaign()

        self.current_campaign = campaign
        self.campaigns.append(campaign)

        await self.reconciliation_reporter.on_campaign_opened(
            campaign_number=len(self.campaigns),
        )

        self.logger.campaign("Opening campaign")

        orders = await self.execution_service.place_orders(order_requests=signal.order_requests)

        self.logger.placed_orders(orders)

        for order in orders:
            if order.status == "FILLED" and order.order_type == "MARKET":
                self.logger.fill_market_order(order, kline)

        campaign.order_ids = [order.order_id for order in orders]
        campaign.mark_open()

        self.logger.campaign("Opened campaign")

    async def _close_campaign(self, signal: StrategySignal, kline: KlineEvent) -> None:
        campaign = self.current_campaign

        if campaign is None:
            self.logger.campaign("Close signal ignored: no current campaign")
            return

        campaign_view = self.current_campaign_view

        if campaign_view is None:
            raise RuntimeError("Current campaign view is not available")

        self.logger.campaign("Closing campaign")
        campaign.begin_closing()

        canceled_orders, close_orders = await self.execution_service.cancel_and_submit_orders(
            orders=list(campaign_view.orders),
            order_ids_to_cancel=signal.cancel_order_ids,
            order_requests=signal.order_requests,
        )

        self.logger.canceled_orders(canceled_orders)
        self.logger.campaign(f"Orders canceled: {len(signal.cancel_order_ids)}")

        self.logger.placed_orders(close_orders)

        for order in close_orders:
            if order.status == "FILLED" and order.order_type == "MARKET":
                self.logger.fill_market_order(order, kline)

        campaign.order_ids.extend([order.order_id for order in close_orders])
        self.logger.campaign(f"Close orders placed: {len(close_orders)}")

        campaign.mark_closed()
        self.logger.campaign("Closed campaign")

        campaign_view = await self.execution_service.get_campaign_view(campaign)

        self.logger.campaign_summary(campaign_view)
        self.logger.campaigns_history(self.campaigns)

        self.current_campaign = None

        await self.reconciliation_reporter.on_campaign_closed(
            campaign=campaign_view,
        )

    def _require_recovery(self, error: Exception) -> None:
        if self.current_campaign is None:
            return

        if self.current_campaign.is_closed:
            return

        self.current_campaign.require_recovery()
        self.logger.campaign(
            f"Recovery required in {self.current_campaign.state.value}: "
            f"{type(error).__name__}: {error}"
        )
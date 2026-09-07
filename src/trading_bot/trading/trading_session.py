from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest
from trading_bot.ports.executor import Executor
from trading_bot.models.campaign import Campaign, CampaignView
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.errors import (
    LimitOrderNotAcceptedError,
    MarketOrderNotAcceptedError,
    MarketOrderNotFullyFilledError,
    OrderCancellationNotCompletedError,
    StrategySignalConflictError, UnexpectedOrderStateError,
)
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.signal import CloseCampaign, NoAction, OpenCampaign
from trading_bot.trading.strategy import Strategy


class TradingSession:

    def __init__(self, strategy: Strategy, executor: Executor, logger: TradingDebugLogger, reconciliation_reporter: PortfolioReconciliationReporter) -> None:
        self.strategy = strategy
        self.executor = executor
        self.logger = logger
        self.reconciliation_reporter = reconciliation_reporter
        self.klines: list[KlineEvent] = []
        self.campaigns: list[Campaign] = []
        self.current_campaign: Campaign | None = None

    async def handle_kline(self, kline: KlineEvent) -> None:
        try:
            await self._handle_kline(kline)
        except Exception as error:
            self._require_recovery(error)
            raise

    async def _handle_kline(self, kline: KlineEvent) -> None:
        if not kline.is_closed:
            return

        self.logger.candle(kline)
        self.klines.append(kline)

        # artifact: needed just for paper executor
        await self.executor.update_executor(kline)

        current_campaign_view: CampaignView | None = await self._get_campaign_view(self.current_campaign)
        account_snapshot: AccountSnapshot = await self.executor.get_account_snapshot()

        signal = self.strategy.on_kline(kline=kline,
                                        klines=self.klines,
                                        current_campaign=current_campaign_view,
                                        account_snapshot=account_snapshot)

        if isinstance(signal, OpenCampaign):
            self.logger.signal("OpenCampaign")
            await self._open_campaign(signal, kline)
            return

        if isinstance(signal, CloseCampaign):
            self.logger.signal("CloseCampaign")
            await self._close_campaign(signal, kline, current_campaign_view)
            return

        if isinstance(signal, NoAction):
            self.logger.signal("NoAction")
            return

        self.logger.signal(f"Unknown signal ignored: {type(signal).__name__}")

    async def _get_campaign_view(self, campaign: Campaign | None) -> CampaignView | None:
        if campaign is None:
            return None

        orders: list[Order] = []

        for order_id in campaign.order_ids:
            order = await self.executor.get_order(order_id)
            orders.append(order)

        return CampaignView(
            state=campaign.state,
            health=campaign.health,
            orders=tuple(orders),
        )

    async def _open_campaign(self, signal: OpenCampaign, kline: KlineEvent) -> None:
        if self.current_campaign is not None:
            self.logger.campaign("Open signal ignored: current campaign already exists")
            return

        self.logger.campaign("Opening campaign")

        campaign = Campaign()

        self.current_campaign = campaign
        self.campaigns.append(campaign)

        await self.reconciliation_reporter.on_campaign_opened(
            campaign_number=len(self.campaigns),
        )

        orders = await self._place_orders(order_requests=signal.order_requests, kline=kline)
        campaign.order_ids = [order.order_id for order in orders]
        campaign.mark_open()

        self.logger.campaign("Opened campaign")

    async def _place_orders(self, order_requests: list[OrderRequest], kline: KlineEvent) -> list[Order]:
        orders: list[Order] = []

        for order_request in order_requests:
            order = await self.executor.place_order(order_request=order_request)
            self._validate_placed_order(order)
            orders.append(order)

        self.logger.placed_orders(orders)

        for order in orders:
            if order.status == "FILLED" and order.request.order_type == "MARKET":
                self.logger.fill_market_order(order, kline)

        return orders

    def _validate_placed_order(self, order: Order) -> None:
        if order.request.order_type == "MARKET":
            if order.status == "REJECTED":
                raise MarketOrderNotAcceptedError(
                    f"Market order #{order.order_id} was not accepted: "
                    f"status={order.status}"
                )

            if order.status != "FILLED":
                raise MarketOrderNotFullyFilledError(
                    f"Market order #{order.order_id} was not fully filled: "
                    f"status={order.status}"
                )

            return

        if order.request.order_type == "LIMIT":
            if order.status == "REJECTED":
                raise LimitOrderNotAcceptedError(
                    f"Limit order #{order.order_id} was not accepted: "
                    f"status={order.status}"
                )

            if order.status not in {"NEW", "PARTIALLY_FILLED", "FILLED"}:
                raise UnexpectedOrderStateError(
                    f"Limit order #{order.order_id} returned an unexpected state "
                    f"after placement: status={order.status}"
                )

            return

        raise ValueError(f"Unsupported order type: {order.request.order_type}")

    async def _close_campaign(self, signal: CloseCampaign, kline: KlineEvent, current_campaign: CampaignView | None) -> None:
        campaign = self.current_campaign

        if campaign is None or current_campaign is None:
            self.logger.campaign("Close signal ignored: no current campaign")
            return

        self.logger.campaign("Closing campaign")

        campaign.begin_closing()

        pending_order_ids = [
            order.order_id
            for order in current_campaign.orders
            if order.status in {"NEW", "PARTIALLY_FILLED"}
        ]

        await self._cancel_orders(orders=list(current_campaign.orders), order_ids_to_cancel=pending_order_ids)
        self.logger.campaign(f"Orders canceled: {len(pending_order_ids)}")

        close_orders = await self._place_orders(order_requests=signal.order_requests, kline=kline)
        campaign.order_ids.extend([order.order_id for order in close_orders])
        self.logger.campaign(f"Close orders placed: {len(close_orders)}")

        campaign.mark_closed()

        campaign_view = await self._get_campaign_view(campaign)

        self.logger.campaign("Closed campaign")
        self.logger.campaign_summary(campaign_view)
        self.logger.campaigns_history(self.campaigns)

        self.current_campaign = None

        await self.reconciliation_reporter.on_campaign_closed(
            campaign=campaign_view,
        )

    async def _cancel_orders(self, orders: list[Order], order_ids_to_cancel: list[str]) -> None:
        canceled_orders: list[Order] = []

        for order in orders:
            if order.order_id not in order_ids_to_cancel:
                continue

            previous_status = order.status
            canceled_order = await self.executor.cancel_order(order)

            if canceled_order.filled_quantity != order.filled_quantity:
                raise StrategySignalConflictError(
                    f"Order #{order.order_id} execution changed while applying the strategy signal: "
                    f"status {order.status} -> {canceled_order.status}, "
                    f"filled quantity {order.filled_quantity} -> {canceled_order.filled_quantity}"
                )

            if canceled_order.status != "CANCELED":
                raise OrderCancellationNotCompletedError(
                    f"Order #{order.order_id} was not canceled: "
                    f"status={canceled_order.status}"
                )

            if previous_status != "CANCELED" and canceled_order.status == "CANCELED":
                canceled_orders.append(canceled_order)

        self.logger.canceled_orders(canceled_orders)

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
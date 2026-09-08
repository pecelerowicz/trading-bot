from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.ports.executor import Executor
from trading_bot.models.campaign import Campaign, CampaignView
from trading_bot.trading.campaign_service import CampaignService
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.signal import CloseCampaign, NoAction, OpenCampaign
from trading_bot.trading.strategy import Strategy


class TradingSession:

    def __init__(self, strategy: Strategy, executor: Executor, campaign_service: CampaignService, logger: TradingDebugLogger, reconciliation_reporter: PortfolioReconciliationReporter) -> None:
        self.strategy = strategy
        self.executor = executor
        self.campaign_service = campaign_service
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

        current_campaign_view: CampaignView | None = None

        if self.current_campaign is not None:
            current_campaign_view = await self._get_campaign_view(self.current_campaign)

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
            await self._close_campaign(signal, kline)
            return

        if isinstance(signal, NoAction):
            self.logger.signal("NoAction")
            return

        self.logger.signal(f"Unknown signal ignored: {type(signal).__name__}")

    async def _get_campaign_view(self, campaign: Campaign) -> CampaignView:
        orders = await self.campaign_service.get_orders(campaign)

        return CampaignView(
            state=campaign.state,
            health=campaign.health,
            orders=orders,
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

        await self.campaign_service.open(campaign=campaign, order_requests=signal.order_requests, kline=kline)

        self.logger.campaign("Opened campaign")

    async def _close_campaign(self, signal: CloseCampaign, kline: KlineEvent) -> None:
        campaign = self.current_campaign

        if campaign is None:
            self.logger.campaign("Close signal ignored: no current campaign")
            return

        self.logger.campaign("Closing campaign")

        await self.campaign_service.close(campaign=campaign, order_requests=signal.order_requests, kline=kline)

        campaign_view = await self._get_campaign_view(campaign)

        self.logger.campaign("Closed campaign")
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
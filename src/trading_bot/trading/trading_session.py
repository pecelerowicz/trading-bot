from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.campaign import Campaign, CampaignView
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.portfolio_reconciliation_reporter import PortfolioReconciliationReporter
from trading_bot.trading.signal import CloseCampaign, NoAction, OpenCampaign
from trading_bot.trading.strategy import Strategy
from trading_bot.trading.trading_execution_service import TradingExecutionService


class TradingSession:

    def __init__(self, strategy: Strategy, execution_service: TradingExecutionService, logger: TradingDebugLogger, reconciliation_reporter: PortfolioReconciliationReporter) -> None:
        self.strategy = strategy
        self.execution_service = execution_service
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

        await self.execution_service.update_executor(kline)

        signal = await self._get_strategy_signal(kline)
        await self._handle_signal(signal, kline)



    async def _get_strategy_signal(self, kline: KlineEvent) -> OpenCampaign | CloseCampaign | NoAction:
        current_campaign_view: CampaignView | None = await self.execution_service.get_campaign_view(self.current_campaign)
        account_snapshot: AccountSnapshot = await self.execution_service.get_account_snapshot()

        return self.strategy.on_kline(kline=kline,
                                      klines=self.klines,
                                      current_campaign=current_campaign_view,
                                      account_snapshot=account_snapshot)

    async def _handle_signal(self, signal: OpenCampaign | CloseCampaign | NoAction, kline: KlineEvent) -> None:
        self.logger.signal(type(signal).__name__)

        match signal:
            case OpenCampaign():
                await self._open_campaign(signal, kline)

            case CloseCampaign():
                await self._close_campaign(signal, kline)

            case NoAction():
                return

            case _:
                raise TypeError(f"Unsupported strategy signal: {type(signal).__name__}")

    async def _open_campaign(self, signal: OpenCampaign, kline: KlineEvent) -> None:
        if self.current_campaign is not None:
            self.logger.campaign("Open signal ignored: current campaign already exists")
            return

        campaign = Campaign()

        self.current_campaign = campaign
        self.campaigns.append(campaign)

        await self.reconciliation_reporter.on_campaign_opened(
            campaign_number=len(self.campaigns),
        )

        await self.execution_service.open_campaign(campaign=campaign, order_requests=signal.order_requests, kline=kline)

    async def _close_campaign(self, signal: CloseCampaign, kline: KlineEvent) -> None:
        campaign = self.current_campaign

        if campaign is None:
            self.logger.campaign("Close signal ignored: no current campaign")
            return

        await self.execution_service.close_campaign(campaign=campaign, order_requests=signal.order_requests, kline=kline)

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
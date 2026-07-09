from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.order import Order, OrderRequest
from trading_bot.trading.signal import CloseCampaign, NoAction, OpenCampaign
from trading_bot.trading.campaign import Campaign


class TradingSession:
    def __init__(self, strategy, executor, logger: TradingDebugLogger) -> None:
        self.strategy = strategy
        self.executor = executor
        self.logger = logger
        self.klines: list[KlineEvent] = []
        self.campaigns: list[Campaign] = []
        self.current_campaign: Campaign | None = None

    async def handle_kline(self, kline: KlineEvent) -> bool:
        if not kline.is_closed:
            return False

        self.logger.candle(kline)
        self.klines.append(kline)
        await self._sync_current_campaign_orders(kline)

        signal = self.strategy.on_kline(kline=kline, klines=self.klines, current_campaign=self.current_campaign)

        if isinstance(signal, OpenCampaign):
            self.logger.signal("OpenCampaign")
            await self._open_campaign(signal, kline)
            return False

        if isinstance(signal, CloseCampaign):
            self.logger.signal("CloseCampaign")
            await self._close_campaign(signal, kline)
            return False

        if isinstance(signal, NoAction):
            self.logger.signal("NoAction")
            return False

        self.logger.signal(f"Unknown signal ignored: {type(signal).__name__}")
        return False

    async def _sync_current_campaign_orders(self, kline: KlineEvent) -> None:
        if self.current_campaign is None:
            return

        updated_orders = []

        for order in self.current_campaign.orders:
            updated = await self.executor.sync_order_status(order, kline)
            updated_orders.append(updated)

        self.current_campaign.orders = updated_orders

    async def _open_campaign(self, signal: OpenCampaign, kline: KlineEvent) -> None:
        if self.current_campaign is not None:
            self.logger.campaign("Open signal ignored: current campaign already exists")
            return

        orders = await self._place_orders(order_requests=signal.order_requests, kline=kline)

        campaign = Campaign(orders=orders, is_active=True)

        self.current_campaign = campaign
        self.campaigns.append(campaign)

        self.logger.campaign("Opened campaign")
        self.logger.campaign_summary(campaign)
        self.logger.campaign_history(self.campaigns)

    async def _close_campaign(self, signal: CloseCampaign, kline: KlineEvent) -> None:
        if self.current_campaign is None:
            self.logger.campaign("Close signal ignored: no current campaign")
            return

        self.current_campaign.orders = await self.executor.cancel_orders(
            orders=self.current_campaign.orders,
            order_ids_to_cancel=signal.order_ids_to_cancel,
        )

        close_orders = await self._place_orders(order_requests=signal.order_requests, kline=kline)

        self.current_campaign.orders.extend(close_orders)
        self.current_campaign.is_active = False

        self.logger.campaign("Closed campaign")
        self.logger.campaign(f"Close orders placed: {len(close_orders)}")
        self.logger.campaign(f"Orders canceled: {len(signal.order_ids_to_cancel)}")
        self.logger.campaign_summary(self.current_campaign)
        self.logger.campaign_history(self.campaigns)

        self.current_campaign = None

    async def _place_orders(self, order_requests: list[OrderRequest], kline: KlineEvent, ) -> list[Order]:
        orders: list[Order] = []

        for order_request in order_requests:
            order = await self.executor.place_order(order_request=order_request, kline=kline)
            orders.append(order)

        return orders
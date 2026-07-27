from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.campaign import Campaign
from trading_bot.trading.signal import CloseCampaign, NoAction, OpenCampaign


class Strategy(Protocol):
    def on_no_campaign(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        account_snapshot: AccountSnapshot
    ) -> OpenCampaign | NoAction:
        ...

    def on_open_campaign(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign: Campaign,
        account_snapshot: AccountSnapshot
    ) -> CloseCampaign | NoAction:
        ...

    def on_closing_campaign(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign: Campaign,
        account_snapshot: AccountSnapshot
    ) -> CloseCampaign | NoAction:
        ...
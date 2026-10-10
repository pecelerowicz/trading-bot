from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.campaign import CampaignView
from trading_bot.trading.signal import StrategySignal


class Strategy(Protocol):
    def create_signal(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign_view: CampaignView | None,
        account_snapshot: AccountSnapshot
    ) -> StrategySignal | None:
        ...
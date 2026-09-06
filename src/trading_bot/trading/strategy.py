from typing import Protocol

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.campaign import CampaignView
from trading_bot.trading.signal import StrategySignal


class Strategy(Protocol):
    def on_kline(
        self,
        kline: KlineEvent,
        klines: list[KlineEvent],
        current_campaign: CampaignView | None,
        account_snapshot: AccountSnapshot
    ) -> StrategySignal:
        ...
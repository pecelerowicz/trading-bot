from dataclasses import dataclass

from trading_bot.trading.order import OrderRequest


@dataclass(frozen=True)
class StartTrade:
    reason: str
    order_requests: list[OrderRequest]


@dataclass(frozen=True)
class ExitTrade:
    reason: str


StrategyResult = StartTrade | ExitTrade | None
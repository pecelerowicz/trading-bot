from dataclasses import dataclass

from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.trading_decision import TradingDecision


@dataclass(frozen=True)
class ExecutionResult:
    action: str
    quantity: float
    fill_price: float
    reason: str = ""


class PaperExecutor:
    async def execute(self, decision: TradingDecision, kline: KlineEvent) -> ExecutionResult | None:
        if decision.action == "HOLD":
            return None

        return ExecutionResult(
            action=decision.action,
            quantity=decision.quantity,
            fill_price=kline.close,
            reason=decision.reason,
        )
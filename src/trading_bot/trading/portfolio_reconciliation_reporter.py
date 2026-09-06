from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from trading_bot.models.account import AccountSnapshot
from trading_bot.models.instrument import Instrument
from trading_bot.models.order import Order
from trading_bot.ports.executor import Executor
from trading_bot.trading.campaign import CampaignView


class PortfolioReconciliationReporter:
    def __init__(self, executor: Executor, instrument: Instrument, output_directory: str = "logs") -> None:
        self.executor = executor
        self.instrument = instrument
        self.current_campaign_number: int | None = None
        self.account_before: AccountSnapshot | None = None

        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        self.file_path = output_path / f"portfolio-reconciliation-{run_id}.log"

    async def on_campaign_opened(self, campaign_number: int) -> None:
        self.current_campaign_number = campaign_number
        self.account_before = await self.executor.get_account_snapshot()

    async def on_campaign_closed(self, campaign: CampaignView) -> None:
        if self.current_campaign_number is None or self.account_before is None:
            raise RuntimeError("Missing opening snapshot for current campaign")

        campaign_number = self.current_campaign_number
        account_after = await self.executor.get_account_snapshot()
        summary = campaign.execution_summary()

        base_before = self.account_before.get_balance(self.instrument.base_asset).total
        base_after = account_after.get_balance(self.instrument.base_asset).total
        quote_before = self.account_before.get_balance(self.instrument.quote_asset).total
        quote_after = account_after.get_balance(self.instrument.quote_asset).total

        portfolio_base_delta = base_after - base_before
        portfolio_quote_delta = quote_after - quote_before

        base_difference = portfolio_base_delta - summary.net_base_delta
        quote_difference = portfolio_quote_delta - summary.net_quote_delta

        consistent = (
            base_difference == Decimal("0")
            and quote_difference == Decimal("0")
        )

        lines = [
            "=" * 80,
            f"CAMPAIGN #{campaign_number} — PORTFOLIO RECONCILIATION",
            "=" * 80,
            "",
            "[1] PORTFOLIO — OBSERVED FROM ACCOUNT SNAPSHOTS",
            "",
            (
                f"    {'ASSET':<8}"
                f"{'BEFORE':>20}"
                f"{'AFTER':>20}"
                f"{'DELTA':>20}"
            ),
            (
                f"    {self.instrument.base_asset:<8}"
                f"{base_before:>20.8f}"
                f"{base_after:>20.8f}"
                f"{portfolio_base_delta:>+20.8f}"
            ),
            (
                f"    {self.instrument.quote_asset:<8}"
                f"{quote_before:>20.2f}"
                f"{quote_after:>20.2f}"
                f"{portfolio_quote_delta:>+20.2f}"
            ),
            "",
            "",
            "[2] CAMPAIGN — CALCULATED FROM ORDER EXECUTIONS",
            "",
            "    EXECUTED ORDERS",
            *self._executed_order_lines(campaign.orders),
            "",
            "    NON-EXECUTED ORDERS",
            *self._non_executed_order_lines(campaign.orders),
            "",
            "    CAMPAIGN DELTA CALCULATED FROM ORDERS",
            f"        {self.instrument.base_asset:<5}= {summary.net_base_delta:+.8f}",
            f"        {self.instrument.quote_asset:<5}= {summary.net_quote_delta:+.2f}",
            "",
            "",
            "[3] RECONCILIATION",
            "",
            "    DIFFERENCE = OBSERVED PORTFOLIO DELTA - CAMPAIGN DELTA",
            "",
            (
                f"    {'ASSET':<8}"
                f"{'PORTFOLIO DELTA':>20}"
                f"{'CAMPAIGN DELTA':>20}"
                f"{'DIFFERENCE':>20}"
            ),
            (
                f"    {self.instrument.base_asset:<8}"
                f"{portfolio_base_delta:>+20.8f}"
                f"{summary.net_base_delta:>+20.8f}"
                f"{base_difference:>+20.8f}"
            ),
            (
                f"    {self.instrument.quote_asset:<8}"
                f"{portfolio_quote_delta:>+20.2f}"
                f"{summary.net_quote_delta:>+20.2f}"
                f"{quote_difference:>+20.2f}"
            ),
            "",
            f"    RESULT: {'CONSISTENT' if consistent else 'INCONSISTENT'}",
            "",
        ]

        with self.file_path.open("a", encoding="utf-8") as reconciliation_file:
            reconciliation_file.write("\n".join(lines) + "\n")

        self.current_campaign_number = None
        self.account_before = None

    def _executed_order_lines(self, orders: tuple[Order, ...]) -> list[str]:
        executed_orders = [
            order
            for order in orders
            if order.filled_quantity > Decimal("0")
        ]

        if not executed_orders:
            return ["        none"]

        return [
            (
                f"        #{order.order_id:<5}"
                f"{order.request.side:<5}"
                f"{order.request.order_type:<9}"
                f"status={order.status:<18}"
                f"filled={order.filled_quantity:<14}"
                f"avg_price={order.average_fill_price}"
            )
            for order in executed_orders
        ]

    def _non_executed_order_lines(self, orders: tuple[Order, ...]) -> list[str]:
        non_executed_orders = [
            order
            for order in orders
            if order.filled_quantity == Decimal("0")
        ]

        if not non_executed_orders:
            return ["        none"]

        orders_by_status: dict[str, list[str]] = {}

        for order in non_executed_orders:
            orders_by_status.setdefault(order.status, []).append(
                f"#{order.order_id}"
            )

        return [
            f"        {status:<18} {', '.join(order_ids)}"
            for status, order_ids in orders_by_status.items()
        ]
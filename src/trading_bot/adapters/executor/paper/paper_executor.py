from dataclasses import replace
from decimal import Decimal

from trading_bot.models.account import AssetBalance, AccountSnapshot
from trading_bot.models.instrument import Instrument
from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.models.order import Order, OrderRequest


class PaperExecutor:
    def __init__(self, logger: TradingDebugLogger, instrument: Instrument, initial_account: AccountSnapshot) -> None:
        self._next_order_id = 1
        self._logger = logger
        self._instrument = instrument
        self._orders: dict[str, Order] = {}
        self._balances: dict[str, AssetBalance] = {
            balance.asset: balance
            for balance in initial_account.balances
        }

        required_assets = {
            instrument.base_asset,
            instrument.quote_asset,
        }

        missing_assets = required_assets.difference(self._balances)

        if missing_assets:
            raise ValueError(
                f"Missing initial balances for: {sorted(missing_assets)}"
            )

    async def process_kline(self, kline: KlineEvent) -> None:
        for order_id, order in tuple(self._orders.items()):
            if order.status not in {"NEW", "PARTIALLY_FILLED"}:
                continue

            request = order.request

            if request.order_type != "LIMIT" or request.price is None:
                continue

            buy_filled = request.side == "BUY" and kline.low <= request.price
            sell_filled = request.side == "SELL" and kline.high >= request.price

            if not (buy_filled or sell_filled):
                continue

            updated_order = replace(
                order,
                status="FILLED",
                filled_quantity=request.quantity,
                average_fill_price=request.price,
            )

            self._orders[order_id] = updated_order
            self._logger.fill_limit_order(updated_order, kline)

    async def place_order(self, order_request: OrderRequest, kline: KlineEvent) -> Order:
        order_id = str(self._next_order_id)
        self._next_order_id += 1

        if order_request.quantity <= 0:
            order = Order(
                order_id=order_id,
                request=order_request,
                status="REJECTED",
                filled_quantity=Decimal("0.0"),
                average_fill_price=None,
            )

        elif order_request.order_type == "MARKET":
            order = Order(
                order_id=order_id,
                request=order_request,
                status="FILLED",
                filled_quantity=order_request.quantity,
                average_fill_price=kline.close,
            )

        else:
            order = Order(
                order_id=order_id,
                request=order_request,
                status="NEW",
                filled_quantity=Decimal("0.0"),
                average_fill_price=None,
            )

        self._orders[order_id] = order
        return order

    async def cancel_order(self, order: Order) -> Order:
        try:
            stored_order = self._orders[order.order_id]
        except KeyError as error:
            raise KeyError(f"Unknown paper order: {order.order_id}") from error

        if stored_order.status not in {"NEW", "PARTIALLY_FILLED"}:
            return stored_order

        updated_order = replace(
            stored_order,
            status="CANCELED",
        )

        self._orders[order.order_id] = updated_order
        return updated_order

    async def sync_order_status(self, order: Order, kline: KlineEvent) -> Order:
        del kline

        try:
            return self._orders[order.order_id]
        except KeyError as error:
            raise KeyError(f"Unknown paper order: {order.order_id}") from error

    async def get_account_snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            balances=tuple(
                self._balances[asset]
                for asset in sorted(self._balances)
            )
        )
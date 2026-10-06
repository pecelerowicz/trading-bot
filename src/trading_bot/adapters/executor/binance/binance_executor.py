import asyncio
from decimal import Decimal
from typing import Any

from binance import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException

from trading_bot.errors import (
    OrderCancellationOutcomeUnknownError,
    OrderCancellationRejectedError,
    OrderNotFoundError,
    OrderPlacementOutcomeUnknownError,
    OrderRejectedError,
    OrderRetrievalError,
)
from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest, OrderStatus


class BinanceExecutor:
    def __init__(self, client: AsyncClient, instrument: Instrument) -> None:
        self._client = client
        self._instrument = instrument

    async def update_executor(self, kline: KlineEvent) -> None:
        pass

    async def place_order(self, order_request: OrderRequest) -> Order:
        order_parameters = self._build_order_parameters(order_request)

        try:
            raw_order = await self._client.create_order(**order_parameters)
        except BinanceAPIException as error:
            if error.code in {-1006, -1007} or error.status_code >= 500:
                raise OrderPlacementOutcomeUnknownError(str(error)) from error

            raise OrderRejectedError(str(error)) from error
        except (BinanceRequestException, asyncio.TimeoutError) as error:
            raise OrderPlacementOutcomeUnknownError(str(error)) from error

        if raw_order["status"] == "REJECTED":
            raise OrderRejectedError("Binance rejected the order")

        return self._map_order(raw_order=raw_order)

    def _build_order_parameters(self, order_request: OrderRequest) -> dict[str, Any]:
        order_parameters: dict[str, Any] = {
            "symbol": self._instrument.symbol,
            "side": order_request.side,
            "type": order_request.order_type,
            "quantity": str(order_request.quantity),
            "newOrderRespType": "RESULT",
        }

        if order_request.order_type == "LIMIT":
            order_parameters["timeInForce"] = "GTC"
            order_parameters["price"] = str(order_request.price)

        return order_parameters

    async def get_order(self, order_id: str) -> Order:
        binance_order_id = int(order_id)

        try:
            raw_order = await self._client.get_order(
                symbol=self._instrument.symbol,
                orderId=binance_order_id,
            )
        except BinanceAPIException as error:
            if error.code == -2013:
                raise OrderNotFoundError(
                    f"Order {order_id} was not found"
                ) from error

            raise OrderRetrievalError(str(error)) from error
        except (BinanceRequestException, asyncio.TimeoutError) as error:
            raise OrderRetrievalError(str(error)) from error

        try:
            return self._map_order(raw_order=raw_order)
        except (KeyError, TypeError, ValueError, ArithmeticError) as error:
            raise OrderRetrievalError(f"Invalid Binance response for order {order_id}") from error

    async def cancel_order(self, order_id: str) -> Order:
        binance_order_id = int(order_id)

        try:
            raw_order = await self._client.cancel_order(symbol=self._instrument.symbol,orderId=binance_order_id)
        except BinanceAPIException as error:
            if error.code in {-1006, -1007} or error.status_code >= 500:
                raise OrderCancellationOutcomeUnknownError(str(error)) from error

            raise OrderCancellationRejectedError(str(error)) from error
        except (BinanceRequestException, asyncio.TimeoutError) as error:
            raise OrderCancellationOutcomeUnknownError(str(error)) from error

        try:
            return self._map_order(raw_order=raw_order)
        except (KeyError, TypeError, ValueError, ArithmeticError) as error:
            raise OrderCancellationOutcomeUnknownError(f"Invalid Binance response while canceling order {order_id}") from error

    async def get_account_snapshot(self) -> AccountSnapshot:
        raw_account = await self._client.get_account()

        return AccountSnapshot(
            balances=(
                self._get_asset_balance(raw_account=raw_account, asset=self._instrument.base_asset),
                self._get_asset_balance(raw_account=raw_account, asset=self._instrument.quote_asset),
            )
        )

    def _map_order(self, raw_order: dict[str, Any]) -> Order:
        filled_quantity = Decimal(raw_order.get("executedQty", "0"))
        filled_quote_quantity = Decimal(raw_order.get("cummulativeQuoteQty", "0"))

        average_fill_price = None
        if filled_quantity > Decimal("0"):
            average_fill_price = filled_quote_quantity / filled_quantity

        order_type = raw_order["type"]

        if order_type not in {"MARKET", "LIMIT"}:
            raise ValueError(f"Unsupported Binance order type: {order_type}")

        price = None
        if order_type == "LIMIT":
            price = Decimal(raw_order["price"])

        return Order(
            order_id=str(raw_order["orderId"]),
            side=raw_order["side"],
            order_type=order_type,
            quantity=Decimal(raw_order["origQty"]),
            price=price,
            status=self._map_order_status(
                status=raw_order["status"],
                filled_quantity=filled_quantity,
            ),
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price,
        )

    def _map_order_status(self, status: str, filled_quantity: Decimal) -> OrderStatus:
        status_mapping: dict[str, OrderStatus] = {
            "NEW": "NEW",
            "PARTIALLY_FILLED": "PARTIALLY_FILLED",
            "FILLED": "FILLED",
            "CANCELED": "CANCELED",
            "EXPIRED": "CANCELED",
            "EXPIRED_IN_MATCH": "CANCELED",
        }

        if status in status_mapping:
            return status_mapping[status]

        if status in {"PENDING_NEW", "PENDING_CANCEL"}:
            if filled_quantity > Decimal("0"):
                return "PARTIALLY_FILLED"

            return "NEW"

        raise ValueError(f"Unsupported Binance order status: {status}")

    def _get_asset_balance(self, raw_account: dict[str, Any], asset: str) -> AssetBalance:
        for raw_balance in raw_account.get("balances", []):
            if raw_balance["asset"] != asset:
                continue

            return AssetBalance(
                asset=asset,
                free=Decimal(raw_balance["free"]),
                locked=Decimal(raw_balance["locked"]),
            )

        return AssetBalance(
            asset=asset,
            free=Decimal("0"),
            locked=Decimal("0"),
        )
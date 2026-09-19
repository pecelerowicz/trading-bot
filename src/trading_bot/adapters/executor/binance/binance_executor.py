import asyncio
from decimal import Decimal
from typing import Any

from binance import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException

from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.models.kline_event import KlineEvent
from trading_bot.models.order import Order, OrderRequest, OrderStatus, OrderType
from trading_bot.ports.executor import ExecutorResult, ExecutorResultStatus


class BinanceExecutor:
    def __init__(self, client: AsyncClient, instrument: Instrument) -> None:
        self._client = client
        self._instrument = instrument

    async def update_executor(self, kline: KlineEvent) -> None:
        pass

    async def place_order(self, order_request: OrderRequest) -> ExecutorResult[Order]:
        order_parameters = {
            "symbol": self._instrument.symbol,
            "side": order_request.side,
            "type": order_request.order_type,
            "quantity": str(order_request.quantity),
            "newOrderRespType": "RESULT",
        }

        if order_request.order_type == "LIMIT":
            if order_request.price is None:
                raise ValueError("Limit order requires a price")

            order_parameters["timeInForce"] = "GTC"
            order_parameters["price"] = str(order_request.price)

        try:
            raw_order = await self._client.create_order(**order_parameters)
        except BinanceAPIException as error:
            return self._map_api_error(error)
        except (BinanceRequestException, asyncio.TimeoutError) as error:
            return ExecutorResult(status=ExecutorResultStatus.UNKNOWN, message=str(error))

        return ExecutorResult(
            status=ExecutorResultStatus.SUCCESS,
            value=self._map_order(raw_order),
        )

    async def get_order(self, order_id: str) -> ExecutorResult[Order]:
        try:
            raw_order = await self._client.get_order(
                symbol=self._instrument.symbol,
                orderId=int(order_id),
            )
        except BinanceAPIException as error:
            return self._map_api_error(error)
        except (BinanceRequestException, asyncio.TimeoutError) as error:
            return ExecutorResult(status=ExecutorResultStatus.UNKNOWN, message=str(error))

        return ExecutorResult(
            status=ExecutorResultStatus.SUCCESS,
            value=self._map_order(raw_order),
        )

    async def cancel_order(self, order_id: str) -> ExecutorResult[Order]:
        try:
            raw_order = await self._client.cancel_order(
                symbol=self._instrument.symbol,
                orderId=int(order_id),
            )
        except BinanceAPIException as error:
            return self._map_api_error(error)
        except (BinanceRequestException, asyncio.TimeoutError) as error:
            return ExecutorResult(status=ExecutorResultStatus.UNKNOWN, message=str(error))

        return ExecutorResult(
            status=ExecutorResultStatus.SUCCESS,
            value=self._map_order(raw_order),
        )

    async def get_account_snapshot(self) -> AccountSnapshot:
        raw_account = await self._client.get_account()

        return AccountSnapshot(
            balances=(
                self._get_asset_balance(raw_account=raw_account, asset=self._instrument.base_asset),
                self._get_asset_balance(raw_account=raw_account, asset=self._instrument.quote_asset),
            )
        )

    def _map_order(self, raw_order: dict[str, Any]) -> Order:
        order_type = self._map_order_type(raw_order["type"])
        filled_quantity = Decimal(raw_order.get("executedQty", "0"))
        filled_quote_quantity = Decimal(raw_order.get("cummulativeQuoteQty", "0"))

        average_fill_price = None
        if filled_quantity > Decimal("0"):
            average_fill_price = filled_quote_quantity / filled_quantity

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

    def _map_order_type(self, order_type: str) -> OrderType:
        if order_type not in {"MARKET", "LIMIT"}:
            raise ValueError(f"Unsupported Binance order type: {order_type}")

        return order_type

    def _map_order_status(self, status: str, filled_quantity: Decimal) -> OrderStatus:
        status_mapping: dict[str, OrderStatus] = {
            "NEW": "NEW",
            "PARTIALLY_FILLED": "PARTIALLY_FILLED",
            "FILLED": "FILLED",
            "CANCELED": "CANCELED",
            "REJECTED": "REJECTED",
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

    def _map_api_error(self, error: BinanceAPIException) -> ExecutorResult[Order]:
        if error.code in {-1006, -1007} or error.status_code >= 500:
            return ExecutorResult(status=ExecutorResultStatus.UNKNOWN, message=str(error))

        return ExecutorResult(status=ExecutorResultStatus.FAILED, message=str(error))

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
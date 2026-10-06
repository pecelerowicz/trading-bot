from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from trading_bot.errors import InvalidOrderRequestError

OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]

@dataclass(frozen=True)
class OrderRequest:
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None

    def __post_init__(self) -> None:
        if self.side not in {"BUY", "SELL"}:
            raise InvalidOrderRequestError(f"Unsupported order side: {self.side}")

        if self.order_type not in {"MARKET", "LIMIT"}:
            raise InvalidOrderRequestError(f"Unsupported order type: {self.order_type}")

        if self.quantity <= Decimal("0"):
            raise InvalidOrderRequestError("Order quantity must be positive")

        if self.order_type == "MARKET":
            if self.price is not None:
                raise InvalidOrderRequestError("Market order must not define a price")
            return

        if self.price is None:
            raise InvalidOrderRequestError("Limit order requires a price")

        if self.price <= Decimal("0"):
            raise InvalidOrderRequestError("Limit order price must be positive")


OrderStatus = Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED"]

@dataclass(frozen=True)
class Order:
    order_id: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None
    status: OrderStatus
    filled_quantity: Decimal = Decimal("0.0")
    average_fill_price: Decimal | None = None
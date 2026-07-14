from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]

@dataclass(frozen=True)
class OrderRequest:
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None


OrderStatus = Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "REJECTED"]

@dataclass(frozen=True)
class Order:
    order_id: str
    request: OrderRequest
    status: OrderStatus
    filled_quantity: Decimal = Decimal("0.0")
    average_fill_price: Decimal | None = None
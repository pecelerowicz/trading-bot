from dataclasses import dataclass
from typing import Literal


OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]

OrderStatus = Literal[
    "NEW",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELED",
    "REJECTED",
]


@dataclass(frozen=True)
class OrderRequest:
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None


@dataclass
class Order:
    order_id: str
    request: OrderRequest
    status: OrderStatus
    filled_quantity: float = 0.0
    average_fill_price: float | None = None
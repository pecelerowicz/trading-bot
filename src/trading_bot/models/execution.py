from dataclasses import dataclass
from typing import Literal

from trading_bot.models.order import Order, OrderRequest


# SUCCESS:
#     The operation completed as requested.
# FAILURE:
#     The operation definitively failed.
# UNKNOWN:
#     It cannot be determined whether the operation was performed.
# NOT_EXECUTED:
#     The operation was not attempted because an earlier operation stopped execution.
# UNEXPECTED_RESULT:
#     The operation completed, but returned a valid order in an unexpected state.
# STATE_CHANGED:
#     The requested operation could not be performed because the order state changed,
#     but the current order state is known.
OperationStatus = Literal[
    "SUCCESS",
    "FAILURE",
    "UNKNOWN",
    "NOT_EXECUTED",
    "UNEXPECTED_RESULT",
    "STATE_CHANGED",
]


@dataclass(frozen=True, kw_only=True)
class Operation:
    status: OperationStatus
    order: Order | None = None


@dataclass(frozen=True, kw_only=True)
class Cancellation(Operation):
    order_id: str


@dataclass(frozen=True, kw_only=True)
class Placement(Operation):
    order_request: OrderRequest


@dataclass(frozen=True)
class Execution:
    cancellations: tuple[Cancellation, ...] = ()
    placements: tuple[Placement, ...] = ()
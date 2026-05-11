from dataclasses import dataclass


@dataclass
class PositionState:
    is_open: bool = False
    entry_price: float | None = None
    quantity: float = 0.0
from dataclasses import dataclass

from trading_bot.trading.order import Order


@dataclass
class Campaign:
    orders: list[Order]
    is_active: bool = True
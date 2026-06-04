from dataclasses import dataclass

from trading_bot.trading.order import Order


@dataclass
class Trade:
    orders: list[Order]
    is_open: bool = True
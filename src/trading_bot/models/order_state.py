from dataclasses import dataclass
from decimal import Decimal

from trading_bot.models.order import Order


@dataclass(frozen=True)
class OrderFillSummary:
    bought_base: Decimal = Decimal("0.0")
    sold_base: Decimal = Decimal("0.0")

    spent_quote: Decimal = Decimal("0.0")
    received_quote: Decimal = Decimal("0.0")

    net_base_delta: Decimal = Decimal("0.0")
    net_quote_delta: Decimal = Decimal("0.0")

    average_buy_price: Decimal | None = None
    average_sell_price: Decimal | None = None


@dataclass(frozen=True)
class OrderStateSnapshot:
    orders: tuple[Order, ...]

    def fill_summary(self) -> OrderFillSummary:
        bought_base = Decimal("0.0")
        sold_base = Decimal("0.0")

        spent_quote = Decimal("0.0")
        received_quote = Decimal("0.0")

        for order in self.orders:
            if order.filled_quantity <= Decimal("0.0"):
                continue

            if order.average_fill_price is None:
                continue

            base_quantity = order.filled_quantity
            quote_value = order.filled_quantity * order.average_fill_price

            if order.side == "BUY":
                bought_base += base_quantity
                spent_quote += quote_value

            elif order.side == "SELL":
                sold_base += base_quantity
                received_quote += quote_value

        net_base_delta = bought_base - sold_base
        net_quote_delta = received_quote - spent_quote

        average_buy_price = spent_quote / bought_base if bought_base > 0 else None
        average_sell_price = received_quote / sold_base if sold_base > 0 else None

        return OrderFillSummary(
            bought_base=bought_base,
            sold_base=sold_base,
            spent_quote=spent_quote,
            received_quote=received_quote,
            net_base_delta=net_base_delta,
            net_quote_delta=net_quote_delta,
            average_buy_price=average_buy_price,
            average_sell_price=average_sell_price,
        )
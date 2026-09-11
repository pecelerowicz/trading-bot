from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from trading_bot.models.order import Order


class CampaignState(Enum):
    OPENING = "OPENING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class CampaignHealth(Enum):
    NORMAL = "NORMAL"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


@dataclass(frozen=True)
class CampaignExecutionSummary:
    state: CampaignState

    bought_base: Decimal = Decimal("0.0")
    sold_base: Decimal = Decimal("0.0")

    spent_quote: Decimal = Decimal("0.0")
    received_quote: Decimal = Decimal("0.0")

    net_base_delta: Decimal = Decimal("0.0")
    net_quote_delta: Decimal = Decimal("0.0")

    average_buy_price: Decimal | None = None
    average_sell_price: Decimal | None = None


@dataclass
class Campaign:
    order_ids: list[str] = field(default_factory=list)
    _state: CampaignState = field(default=CampaignState.OPENING, init=False, repr=False)
    _health: CampaignHealth = field(default=CampaignHealth.NORMAL, init=False, repr=False)

    @property
    def state(self) -> CampaignState:
        return self._state

    @property
    def health(self) -> CampaignHealth:
        return self._health

    @property
    def is_open(self) -> bool:
        return self.state == CampaignState.OPEN

    @property
    def is_closing(self) -> bool:
        return self.state == CampaignState.CLOSING

    @property
    def is_recovery(self) -> bool:
        return self.health == CampaignHealth.RECOVERY_REQUIRED

    @property
    def is_closed(self) -> bool:
        return self.state == CampaignState.CLOSED

    def mark_open(self) -> None:
        if self.state != CampaignState.OPENING:
            raise RuntimeError(f"Cannot open campaign from state {self.state.value}")

        self._state = CampaignState.OPEN

    def begin_closing(self) -> None:
        if self.state != CampaignState.OPEN:
            raise RuntimeError(f"Cannot close campaign from state {self.state.value}")

        self._state = CampaignState.CLOSING

    def mark_closed(self) -> None:
        if self.state != CampaignState.CLOSING:
            raise RuntimeError(f"Cannot mark campaign as closed from state {self.state.value}")

        self._state = CampaignState.CLOSED

    def require_recovery(self) -> None:
        if self.is_closed:
            return

        self._health = CampaignHealth.RECOVERY_REQUIRED


@dataclass(frozen=True)
class CampaignView:
    state: CampaignState
    health: CampaignHealth
    orders: tuple[Order, ...]

    @property
    def is_open(self) -> bool:
        return self.state == CampaignState.OPEN

    @property
    def is_closing(self) -> bool:
        return self.state == CampaignState.CLOSING

    @property
    def is_recovery(self) -> bool:
        return self.health == CampaignHealth.RECOVERY_REQUIRED

    @property
    def is_closed(self) -> bool:
        return self.state == CampaignState.CLOSED

    def execution_summary(self) -> CampaignExecutionSummary:
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

            if order.request.side == "BUY":
                bought_base += base_quantity
                spent_quote += quote_value

            elif order.request.side == "SELL":
                sold_base += base_quantity
                received_quote += quote_value

        net_base_delta = bought_base - sold_base
        net_quote_delta = received_quote - spent_quote

        average_buy_price = spent_quote / bought_base if bought_base > 0 else None
        average_sell_price = received_quote / sold_base if sold_base > 0 else None

        return CampaignExecutionSummary(
            state=self.state,
            bought_base=bought_base,
            sold_base=sold_base,
            spent_quote=spent_quote,
            received_quote=received_quote,
            net_base_delta=net_base_delta,
            net_quote_delta=net_quote_delta,
            average_buy_price=average_buy_price,
            average_sell_price=average_sell_price,
        )
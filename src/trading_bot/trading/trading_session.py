from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import Order, OrderRequest
from trading_bot.trading.signal import StrategyAction
from trading_bot.trading.trade import Trade


class TradingSession:
    def __init__(self, strategy, executor) -> None:
        self.strategy = strategy
        self.executor = executor
        self.klines: list[KlineEvent] = []
        self.current_trade: Trade | None = None

    async def handle_kline(self, kline: KlineEvent) -> bool:
        if not kline.is_closed:
            return False

        self.klines.append(kline)

        if self.current_trade is not None:
            self.current_trade.orders = await self.executor.refresh_orders(
                orders=self.current_trade.orders,
                kline=kline,
            )

            if self._should_close_current_trade():
                print("Trade completed")
                self.current_trade = None

        action = self.strategy.on_kline(
            kline=kline,
            klines=self.klines,
            current_trade=self.current_trade,
        )

        print(action)

        if not action.has_orders:
            return False

        await self._handle_strategy_action(
            action=action,
            kline=kline,
        )

        return False

    async def _handle_strategy_action(
        self,
        action: StrategyAction,
        kline: KlineEvent,
    ) -> None:
        created_orders = await self._place_orders(
            order_requests=action.order_requests,
            kline=kline,
        )

        if self.current_trade is None:
            self.current_trade = Trade(
                reason=action.reason,
                orders=created_orders,
            )

            print(f"Trade started: {self.current_trade.reason}")
            return

        self.current_trade.orders.extend(created_orders)
        print(f"Added orders to current trade: {len(created_orders)}")

        if self._should_close_current_trade():
            print("Trade completed")
            self.current_trade = None

    async def _place_orders(
        self,
        order_requests: list[OrderRequest],
        kline: KlineEvent,
    ) -> list[Order]:
        orders = []

        for order_request in order_requests:
            order = await self.executor.place_order(
                order_request=order_request,
                kline=kline,
            )
            orders.append(order)

        return orders

    def _should_close_current_trade(self) -> bool:
        if self.current_trade is None:
            return False

        if self.current_trade.has_open_orders:
            return False

        if self.current_trade.net_quantity > 0:
            return False

        return True
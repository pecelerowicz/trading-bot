from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.debug_logger import TradingDebugLogger
from trading_bot.trading.order import Order, OrderRequest
from trading_bot.trading.signal import CloseTrade, NoAction, OpenTrade
from trading_bot.trading.trade import Trade


class TradingSession:
    def __init__(
        self,
        strategy,
        executor,
        debug_logger: TradingDebugLogger | None = None,
    ) -> None:
        self.strategy = strategy
        self.executor = executor
        self.debug_logger = debug_logger
        self.klines: list[KlineEvent] = []
        self.current_trade: Trade | None = None

    async def handle_kline(self, kline: KlineEvent) -> bool:
        if not kline.is_closed:
            return False

        if self.debug_logger is not None:
            self.debug_logger.candle(kline)

        self.klines.append(kline)

        if self.current_trade is not None:
            self.current_trade.orders = await self.executor.sync_order_statuses(
                orders=self.current_trade.orders,
                kline=kline,
            )

        signal = self.strategy.on_kline(
            kline=kline,
            klines=self.klines,
            current_trade=self.current_trade,
        )

        if isinstance(signal, OpenTrade):
            if self.debug_logger is not None:
                self.debug_logger.signal("OpenTrade")
            await self._open_trade(signal, kline)
            return False

        if isinstance(signal, CloseTrade):
            if self.debug_logger is not None:
                self.debug_logger.signal("CloseTrade")
            await self._close_trade(signal, kline)
            return False

        if isinstance(signal, NoAction):
            if self.debug_logger is not None:
                self.debug_logger.signal("NoAction")
            return False

        if self.debug_logger is not None:
            self.debug_logger.signal(f"Unknown signal ignored: {type(signal).__name__}")

        return False

    async def _open_trade(self, signal: OpenTrade, kline: KlineEvent) -> None:
        if self.current_trade is not None:
            if self.debug_logger is not None:
                self.debug_logger.trade(
                    "Open signal ignored: current trade already exists"
                )
            return

        orders = await self._place_orders(
            order_requests=signal.order_requests,
            kline=kline,
        )

        self.current_trade = Trade(
            orders=orders,
            is_open=True,
        )

        if self.debug_logger is not None:
            self.debug_logger.trade(f"Opened trade with {len(orders)} orders")

    async def _close_trade(self, signal: CloseTrade, kline: KlineEvent) -> None:
        if self.current_trade is None:
            if self.debug_logger is not None:
                self.debug_logger.trade("Close signal ignored: no current trade")
            return

        self.current_trade.orders = await self.executor.cancel_orders(
            orders=self.current_trade.orders,
            order_ids_to_cancel=signal.order_ids_to_cancel,
        )

        close_orders = await self._place_orders(
            order_requests=signal.order_requests,
            kline=kline,
        )

        self.current_trade.orders.extend(close_orders)
        self.current_trade.is_open = False

        if self.debug_logger is not None:
            self.debug_logger.trade("Closed trade")
            self.debug_logger.trade(
                f"Close orders placed: {len(close_orders)}"
            )
            self.debug_logger.trade(
                f"Orders canceled: {len(signal.order_ids_to_cancel)}"
            )
            self.debug_logger.trade_orders(self.current_trade.orders)

        self.current_trade = None

    async def _place_orders(
        self,
        order_requests: list[OrderRequest],
        kline: KlineEvent,
    ) -> list[Order]:
        orders: list[Order] = []

        for order_request in order_requests:
            if order_request.quantity <= 0:
                if self.debug_logger is not None:
                    self.debug_logger.order(
                        f"Ignored order request: non-positive quantity "
                        f"({order_request.quantity})"
                    )
                continue

            order = await self.executor.place_order(
                order_request=order_request,
                kline=kline,
            )
            orders.append(order)

        return orders
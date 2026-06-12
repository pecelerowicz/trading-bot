from trading_bot.models.kline_event import KlineEvent
from trading_bot.trading.order import Order, OrderRequest
from trading_bot.trading.signal import CloseTrade, NoAction, OpenTrade
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

        # === DEBUG: Print current kline info (TradingView-style) ===
        if abs(kline.close - kline.open) < 0.0001:
            color = "⚪ DOJI"
        elif kline.close > kline.open:
            color = "🟢 GREEN"
        else:
            color = "🔴 RED"

        price_change_pct = (kline.close - kline.open) / kline.open * 100 if kline.open != 0 else 0

        print()
        print(
            f"{kline.open_time.strftime('%Y-%m-%d %H:%M')} | "
            f"{color} | "
            f"O:{kline.open:.4f} H:{kline.high:.4f} L:{kline.low:.4f} C:{kline.close:.4f} | "
            f"Change: {price_change_pct:+.3f}% | "
            f"Vol: {kline.volume:,.0f}"
        )
        # ========================================================

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

        #print(signal)

        if isinstance(signal, OpenTrade):
            await self._open_trade(signal, kline)
            return False

        if isinstance(signal, CloseTrade):
            await self._close_trade(signal, kline)
            return False

        if isinstance(signal, NoAction):
            return False

        return False

    async def _open_trade(self, signal: OpenTrade, kline: KlineEvent) -> None:
        if self.current_trade is not None:
            print("OpenTrade ignored: current trade already exists")
            return

        orders = await self._place_orders(
            order_requests=signal.order_requests,
            kline=kline,
        )

        self.current_trade = Trade(
            orders=orders,
            is_open=True,
        )

        print(f"Trade opened with {len(orders)} orders")

    async def _close_trade(self, signal: CloseTrade, kline: KlineEvent) -> None:
        if self.current_trade is None:
            print("CloseTrade ignored: no current trade")
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
        self.current_trade = None

        print(
            f"Trade closed with {len(close_orders)} close orders "
            f"and {len(signal.order_ids_to_cancel)} canceled orders"
        )

    async def _place_orders(
        self,
        order_requests: list[OrderRequest],
        kline: KlineEvent,
    ) -> list[Order]:
        orders: list[Order] = []

        for order_request in order_requests:
            if order_request.quantity <= 0:
                print(f"Ignored order with non-positive quantity: {order_request}")
                continue

            order = await self.executor.place_order(
                order_request=order_request,
                kline=kline,
            )
            orders.append(order)

        return orders
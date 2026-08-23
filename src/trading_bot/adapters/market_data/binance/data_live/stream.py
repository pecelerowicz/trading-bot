from binance import AsyncClient, BinanceSocketManager

from trading_bot.adapters.market_data.binance.mappers.ws_kline_mapper import map_ws_kline


class BinanceMarketDataSource:
    def __init__(
        self,
        client: AsyncClient,
        symbol: str,
        interval: str,
    ):
        self._client = client
        self._symbol = symbol
        self._interval = interval

    async def stream_klines(self):
        bm = BinanceSocketManager(self._client)
        ts = bm.kline_socket(
            symbol=self._symbol,
            interval=self._interval,
        )

        async with ts as stream:
            while True:
                raw_msg = await stream.recv()
                yield map_ws_kline(raw_msg)
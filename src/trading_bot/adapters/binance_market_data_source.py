from binance import AsyncClient, BinanceSocketManager

from trading_bot.adapters.binance_ws_kline_mapper import map_ws_kline


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

    @classmethod
    async def create(
        cls,
        environment: str,
        symbol: str,
        interval: str,
    ) -> "BinanceMarketDataSource":
        client = await AsyncClient.create(
            testnet=environment == "testnet",
        )

        return cls(
            client=client,
            symbol=symbol,
            interval=interval,
        )

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

    async def close(self) -> None:
        await self._client.close_connection()
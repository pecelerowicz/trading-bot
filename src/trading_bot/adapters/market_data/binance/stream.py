from binance import BinanceSocketManager, AsyncClient

from trading_bot.adapters.market_data.binance.ws_kline_mapper import map_ws_kline


class BinanceMarketDataSource:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool,
        symbol: str,
        interval: str,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.symbol = symbol
        self.interval = interval

    async def stream_klines(self):
        async_client = await AsyncClient.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=self.testnet,
        )

        try:
            bm = BinanceSocketManager(async_client)
            ts = bm.kline_socket(
                symbol=self.symbol,
                interval=self.interval,
            )

            async with ts as stream:
                while True:
                    raw_msg = await stream.recv()
                    yield map_ws_kline(raw_msg)

        finally:
            await async_client.close_connection()
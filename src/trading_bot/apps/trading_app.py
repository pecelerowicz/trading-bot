from binance import AsyncClient, BinanceSocketManager

from trading_bot.mappers.ws_kline_mapper import map_ws_kline
from trading_bot.trading.trading_session import TradingSession


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


class TradingApp:
    def __init__(
        self,
        market_data_source,
        trading_session: TradingSession,
    ):
        self.market_data_source = market_data_source
        self.trading_session = trading_session

    async def run(self):
        async for kline in self.market_data_source.stream_klines():
            should_stop = await self.trading_session.handle_kline(kline)

            if should_stop:
                break
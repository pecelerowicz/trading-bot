from binance import AsyncClient, BinanceSocketManager

from trading_bot.config import AppConfig
from trading_bot.mappers.ws_kline_mapper import map_ws_kline
from trading_bot.trading.trading_session import TradingSession


class BinanceStreamer:
    def __init__(self, async_client, symbol, interval):
        self.async_client = async_client
        self.symbol = symbol
        self.interval = interval

    async def stream(self, trading_session: TradingSession):
        bm = BinanceSocketManager(self.async_client)
        ts = bm.kline_socket(symbol=self.symbol, interval=self.interval)

        async with ts as stream:
            while True:
                raw_msg = await stream.recv()
                msg = map_ws_kline(raw_msg)
                should_stop = await trading_session.handle_kline(msg)
                if should_stop:
                    break


class BinanceApp:
    def __init__(self, app_config: AppConfig, trading_session: TradingSession):
        self.api_key = app_config.api_key
        self.api_secret = app_config.api_secret
        self.symbol = app_config.symbol
        self.interval = app_config.interval
        self.use_production = app_config.is_production
        self.trading_session = trading_session
        print(app_config.binance_env)

    async def run(self):
        async_client = await AsyncClient.create(
            api_key = self.api_key,
            api_secret = self.api_secret,
            testnet = not self.use_production
        )

        try:
            streamer = BinanceStreamer(async_client, self.symbol, self.interval)
            await streamer.stream(trading_session=self.trading_session)
        finally:
            await async_client.close_connection()
from binance import AsyncClient, BinanceSocketManager

from trading_bot.handlers import handle_message_print

from trading_bot.mappers.ws_kline_mapper import map_ws_kline


class BinanceStreamer:
    def __init__(self, async_client, symbol, interval):
        self.async_client = async_client
        self.symbol = symbol
        self.interval = interval

    async def stream(self, message_handler):
        bm = BinanceSocketManager(self.async_client)
        ts = bm.kline_socket(symbol=self.symbol, interval=self.interval)

        async with ts as stream:
            while True:
                raw_msg = await stream.recv()
                msg = map_ws_kline(raw_msg)
                should_stop = await message_handler(msg)
                if should_stop:
                    break


class BinanceApp:
    def __init__(self, api_key, api_secret, symbol, interval):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.interval = interval

    async def run(self):
        async_client = await AsyncClient.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=True
        )

        try:
            streamer = BinanceStreamer(async_client, self.symbol, self.interval)
            await streamer.stream(handle_message_print)
        finally:
            await async_client.close_connection()
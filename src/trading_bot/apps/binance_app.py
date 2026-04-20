from binance import AsyncClient, BinanceSocketManager

from trading_bot.handlers import handle_message_print


class BinanceStreamer:
    def __init__(self, async_client, symbol):
        self.async_client = async_client
        self.symbol = symbol

    async def stream(self, message_handler):
        bm = BinanceSocketManager(self.async_client)
        ts = bm.symbol_miniticker_socket(symbol=self.symbol)

        async with ts as stream:
            while True:
                msg = await stream.recv()
                should_stop = await message_handler(msg)
                if should_stop:
                    break


class BinanceApp:
    def __init__(self, api_key, api_secret, symbol):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol

    async def run(self):
        async_client = await AsyncClient.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=True
        )

        try:
            streamer = BinanceStreamer(async_client, self.symbol)
            await streamer.stream(handle_message_print)
        finally:
            await async_client.close_connection()
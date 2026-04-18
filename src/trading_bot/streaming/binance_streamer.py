from binance import BinanceSocketManager


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
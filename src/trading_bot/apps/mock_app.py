import asyncio

from trading_bot.handlers import handle_message_print


class MockStreamer:
    def __init__(self):
        self.messages = [
            {"E": 1710000000000, "c": "84123.10"},
            {"E": 1710000001000, "c": "84124.20"},
            {"E": 1710000002000, "c": "84130.00"},
        ]

    async def stream(self, message_handler):
        for msg in self.messages:
            await asyncio.sleep(1)
            should_stop = await message_handler(msg)
            if should_stop:
                break


class MockApp:
    async def run(self):
        streamer = MockStreamer()
        await streamer.stream(handle_message_print)
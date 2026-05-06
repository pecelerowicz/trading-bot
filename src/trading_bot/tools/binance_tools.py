from binance.client import Client
import pandas as pd


class BinanceKlinesRetriever:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key=api_key, api_secret=api_secret)

    def _to_timestamp(self, date_str: str) -> int:
        dt = pd.to_datetime(date_str, utc=True)
        return dt.value // 10**6

    def _interval_to_ms(self, interval: str) -> int:
        mapping = {
            "1d": 86_400_000,
            "4h": 14_400_000,
            "1h": 3_600_000,
            "1m": 60_000
        }
        if interval not in mapping:
            raise ValueError(f"Unsupported interval: {interval}")
        return mapping[interval]

    # TODO this run up is probably to be removed from here (and moved to the mock streamer)
    def get_raw_klines(
        self,
        symbol: str,
        interval: str,
        initial_date: str,
        final_date: str,
        run_up: int = 0,
    ) -> list[list]:
        if run_up < 0:
            raise ValueError("run_up cannot be negative")

        offset = self._interval_to_ms(interval) * run_up
        start_ts = self._to_timestamp(initial_date) - offset
        end_ts = self._to_timestamp(final_date)

        return self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_ts,
            end_str=end_ts,
        )

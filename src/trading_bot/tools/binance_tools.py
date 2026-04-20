from binance.client import Client
import pandas as pd

from trading_bot.mappers.rest_kline_mapper import map_rest_kline


class BinanceBarsRetriever:
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
        }
        if interval not in mapping:
            raise ValueError(f"Unsupported interval: {interval}")
        return mapping[interval]

    def get_klines(
        self,
        symbol: str,
        interval: str,
        initial_date: str,
        final_date: str,
        run_up: int = 0,
    ) -> list:
        if run_up < 0:
            raise ValueError("run_up cannot be negative")

        offset = self._interval_to_ms(interval) * run_up
        start_ts = self._to_timestamp(initial_date) - offset
        end_ts = self._to_timestamp(final_date)

        bars = self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_ts,
            end_str=end_ts,
        )

        return [map_rest_kline(bar) for bar in bars]

    def to_dataframe(self, klines) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "event_time": k.event_time,
                "open_time": k.open_time,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "is_closed": k.is_closed,
            }
            for k in klines
        ])

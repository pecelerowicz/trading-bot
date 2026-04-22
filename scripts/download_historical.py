from dotenv import load_dotenv
import json
import os
from pathlib import Path

from trading_bot.tools.binance_tools import BinanceKlinesRetriever


def main():
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    symbol = "BTCUSDT"
    interval = "1h"
    initial_date = "2024-01-01"
    final_date = "2024-01-02"

    retriever = BinanceKlinesRetriever(api_key=api_key, api_secret=api_secret)

    raw_klines = retriever.get_raw_klines(
        symbol=symbol,
        interval=interval,
        initial_date=initial_date,
        final_date=final_date,
    )

    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)

    file_name = f"{symbol}_{interval}.json"
    file_path = data_dir / file_name

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(raw_klines, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(raw_klines)} raw klines to {file_path}")


if __name__ == "__main__":
    main()
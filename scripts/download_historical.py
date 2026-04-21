from dotenv import load_dotenv
import os
from pathlib import Path

from trading_bot.tools.binance_tools import BinanceBarsRetriever


def main():
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    symbol = "BTCUSDT"
    interval = "1h"

    retriever = BinanceBarsRetriever(api_key=api_key, api_secret=api_secret)

    klines = retriever.get_klines(
        symbol=symbol,
        interval=interval,
        initial_date="2024-01-01",
        final_date="2024-01-02",
    )

    # 👇 konwersja na DataFrame (już masz metodę)
    df = retriever.to_dataframe(klines)

    # 👇 ścieżka do katalogu data (root projektu)
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)

    # 👇 nazwa pliku
    file_name = f"{symbol}_{interval}.csv"
    file_path = data_dir / file_name

    # 👇 zapis (nadpisuje jeśli istnieje)
    df.to_csv(file_path, index=False)

    print(f"Saved {len(df)} rows to {file_path}")


if __name__ == "__main__":
    main()
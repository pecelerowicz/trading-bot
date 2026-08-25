import os
from dataclasses import dataclass
from decimal import Decimal
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    market_data_source: str
    executor: str
    symbol: str
    base_asset: str
    quote_asset: str
    interval: str
    paper_initial_base_balance: Decimal
    paper_initial_quote_balance: Decimal

    binance_api_key_testnet: str | None = None
    binance_api_secret_testnet: str | None = None
    binance_api_key_production: str | None = None
    binance_api_secret_production: str | None = None

    replay_initial_date: str | None = None
    replay_final_date: str | None = None
    replay_delay_seconds: float | None = None


def load_app_config() -> AppConfig:
    load_dotenv()

    market_data_source = os.getenv("MARKET_DATA_SOURCE")
    executor = os.getenv("EXECUTOR")

    if market_data_source not in {"replay_binance", "binance_testnet", "binance_production"}:
        raise ValueError(f"Unsupported market data source: {market_data_source}")

    if executor not in {"paper", "binance_testnet", "binance_production"}:
        raise ValueError(f"Unsupported executor: {executor}")

    if market_data_source == "replay_binance" and executor != "paper":
        raise ValueError("Replay market data can only be used with paper executor")

    if market_data_source == "binance_testnet" and executor == "binance_production":
        raise ValueError("Binance production executor cannot use Binance testnet market data")

    return AppConfig(
        market_data_source=market_data_source,
        executor=executor,
        symbol=os.getenv("SYMBOL"),
        base_asset=os.getenv("BASE_ASSET"),
        quote_asset=os.getenv("QUOTE_ASSET"),
        interval=os.getenv("INTERVAL"),
        paper_initial_base_balance=Decimal(os.getenv("PAPER_INITIAL_BASE_BALANCE", "0")),
        paper_initial_quote_balance=Decimal(os.getenv("PAPER_INITIAL_QUOTE_BALANCE", "0")),
        binance_api_key_testnet=os.getenv("BINANCE_API_KEY_TESTNET"),
        binance_api_secret_testnet=os.getenv("BINANCE_API_SECRET_TESTNET"),
        binance_api_key_production=os.getenv("BINANCE_API_KEY_PRODUCTION"),
        binance_api_secret_production=os.getenv("BINANCE_API_SECRET_PRODUCTION"),
        replay_initial_date=os.getenv("REPLAY_INITIAL_DATE"),
        replay_final_date=os.getenv("REPLAY_FINAL_DATE"),
        replay_delay_seconds=float(os.getenv("REPLAY_DELAY_SECONDS", "0")),
    )
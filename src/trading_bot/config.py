import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    binance_env: str
    symbol: str
    base_asset: str
    quote_asset: str
    interval: str

    api_key: str | None = None
    api_secret: str | None = None

    mock_initial_date: str | None = None
    mock_final_date: str | None = None
    mock_delay_seconds: float | None = None

    @property
    def is_mock(self) -> bool:
        return self.binance_env == "mock"

    @property
    def is_testnet(self) -> bool:
        return self.binance_env == "testnet"

    @property
    def is_production(self) -> bool:
        return self.binance_env == "production"


def load_app_config() -> AppConfig:
    load_dotenv()

    binance_env = os.getenv("BINANCE_ENV")

    if binance_env == "production":
        api_key = os.getenv("BINANCE_API_KEY_PRODUCTION")
        api_secret = os.getenv("BINANCE_API_SECRET_PRODUCTION")
    elif binance_env == "testnet":
        api_key = os.getenv("BINANCE_API_KEY_TESTNET")
        api_secret = os.getenv("BINANCE_API_SECRET_TESTNET")
    else:
        api_key = None
        api_secret = None

    return AppConfig(
        binance_env=binance_env,
        symbol=os.getenv("SYMBOL"),
        base_asset=os.getenv("BASE_ASSET"),
        quote_asset=os.getenv("QUOTE_ASSET"),
        interval=os.getenv("INTERVAL"),
        api_key=api_key,
        api_secret=api_secret,
        mock_initial_date=os.getenv("MOCK_INITIAL_DATE"),
        mock_final_date=os.getenv("MOCK_FINAL_DATE"),
        mock_delay_seconds=float(os.getenv("MOCK_DELAY_SECONDS")),
    )
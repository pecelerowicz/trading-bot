import os
from dataclasses import dataclass
from decimal import Decimal
from dotenv import load_dotenv


@dataclass(frozen=True)
class InstrumentConfig:
    symbol: str
    base_asset: str
    quote_asset: str
    interval: str


@dataclass(frozen=True)
class LiveConfig:
    exchange: str | None
    environment: str | None


@dataclass(frozen=True)
class ReplayConfig:
    file_path: str | None
    mapper: str | None
    initial_date: str | None = None
    final_date: str | None = None
    delay_seconds: float = 0.0


@dataclass(frozen=True)
class ExecutorConfig:
    executor: str
    paper_initial_base_balance: Decimal
    paper_initial_quote_balance: Decimal
    binance_api_key_testnet: str | None = None
    binance_api_secret_testnet: str | None = None
    binance_api_key_production: str | None = None
    binance_api_secret_production: str | None = None


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    instrument: InstrumentConfig
    live: LiveConfig
    replay: ReplayConfig
    executor: ExecutorConfig


def load_runtime_config() -> RuntimeConfig:
    load_dotenv()

    mode = os.getenv("RUNTIME_MODE")
    live_exchange = os.getenv("LIVE_EXCHANGE")
    live_environment = os.getenv("LIVE_ENVIRONMENT")
    replay_file_path = os.getenv("REPLAY_FILE_PATH")
    replay_mapper = os.getenv("REPLAY_MAPPER")
    replay_initial_date = os.getenv("REPLAY_INITIAL_DATE")
    replay_final_date = os.getenv("REPLAY_FINAL_DATE")
    executor = os.getenv("EXECUTOR")

    if mode not in {"live", "replay"}:
        raise ValueError(f"Unsupported runtime mode: {mode}")

    if executor not in {"paper", "binance_testnet", "binance_production"}:
        raise ValueError(f"Unsupported executor: {executor}")

    if mode == "live":
        if live_exchange not in {"binance"}:
            raise ValueError(f"Unsupported live exchange: {live_exchange}")

        if live_environment not in {"testnet", "production"}:
            raise ValueError(f"Unsupported live environment: {live_environment}")

        if live_exchange == "binance" and live_environment == "testnet" and executor == "binance_production":
            raise ValueError("Binance production executor cannot use Binance testnet market data")

    if mode == "replay":
        if not replay_file_path:
            raise ValueError("Replay file path is required")

        if replay_mapper not in {"binance_rest"}:
            raise ValueError(f"Unsupported replay mapper: {replay_mapper}")

        if not replay_initial_date or not replay_final_date:
            raise ValueError("Replay initial and final dates are required")

        if executor != "paper":
            raise ValueError("Replay market data can only be used with paper executor")

    return RuntimeConfig(
        mode=mode,
        instrument=InstrumentConfig(
            symbol=os.getenv("SYMBOL"),
            base_asset=os.getenv("BASE_ASSET"),
            quote_asset=os.getenv("QUOTE_ASSET"),
            interval=os.getenv("INTERVAL"),
        ),
        live=LiveConfig(
            exchange=live_exchange,
            environment=live_environment,
        ),
        replay=ReplayConfig(
            file_path=replay_file_path,
            mapper=replay_mapper,
            initial_date=replay_initial_date,
            final_date=replay_final_date,
            delay_seconds=float(os.getenv("REPLAY_DELAY_SECONDS") or "0"),
        ),
        executor=ExecutorConfig(
            executor=executor,
            paper_initial_base_balance=Decimal(os.getenv("PAPER_INITIAL_BASE_BALANCE", "0")),
            paper_initial_quote_balance=Decimal(os.getenv("PAPER_INITIAL_QUOTE_BALANCE", "0")),
            binance_api_key_testnet=os.getenv("BINANCE_API_KEY_TESTNET"),
            binance_api_secret_testnet=os.getenv("BINANCE_API_SECRET_TESTNET"),
            binance_api_key_production=os.getenv("BINANCE_API_KEY_PRODUCTION"),
            binance_api_secret_production=os.getenv("BINANCE_API_SECRET_PRODUCTION"),
        ),
    )
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    mapper: str | None


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

    mode = _required_env("RUNTIME_MODE")
    executor = _required_env("EXECUTOR")

    if mode not in {"live", "replay"}:
        raise ValueError(
            f"Unsupported RUNTIME_MODE: {mode}"
        )

    if executor not in {
        "paper",
        "binance_testnet",
        "binance_production",
    }:
        raise ValueError(
            f"Unsupported EXECUTOR: {executor}"
        )

    live_exchange = os.getenv("LIVE_EXCHANGE")
    live_environment = os.getenv("LIVE_ENVIRONMENT")
    live_mapper = os.getenv("LIVE_MAPPER")

    replay_file_path = os.getenv("REPLAY_FILE_PATH")
    replay_mapper = os.getenv("REPLAY_MAPPER")
    replay_initial_date = os.getenv("REPLAY_INITIAL_DATE")
    replay_final_date = os.getenv("REPLAY_FINAL_DATE")

    if mode == "live":
        live_exchange = _required_env("LIVE_EXCHANGE")
        live_environment = _required_env("LIVE_ENVIRONMENT")
        live_mapper = _required_env("LIVE_MAPPER")

        if live_exchange != "binance":
            raise ValueError(
                f"Unsupported LIVE_EXCHANGE: {live_exchange}"
            )

        if live_environment not in {
            "testnet",
            "production",
        }:
            raise ValueError(
                f"Unsupported LIVE_ENVIRONMENT: "
                f"{live_environment}"
            )

        if live_mapper != "binance_websocket":
            raise ValueError(
                f"Unsupported LIVE_MAPPER: {live_mapper}"
            )

        if (
            live_environment == "testnet"
            and executor == "binance_production"
        ):
            raise ValueError(
                "LIVE_ENVIRONMENT=testnet cannot use "
                "EXECUTOR=binance_production"
            )

        if (
            live_environment == "production"
            and executor == "binance_testnet"
        ):
            raise ValueError(
                "LIVE_ENVIRONMENT=production cannot use "
                "EXECUTOR=binance_testnet"
            )

    if mode == "replay":
        replay_file_path = _project_path(
            _required_env("REPLAY_FILE_PATH")
        )
        replay_mapper = _required_env(
            "REPLAY_MAPPER"
        )
        replay_initial_date = _required_env(
            "REPLAY_INITIAL_DATE"
        )
        replay_final_date = _required_env(
            "REPLAY_FINAL_DATE"
        )

        if replay_mapper != "binance_rest":
            raise ValueError(
                f"Unsupported REPLAY_MAPPER: "
                f"{replay_mapper}"
            )

        if executor != "paper":
            raise ValueError(
                "RUNTIME_MODE=replay requires "
                "EXECUTOR=paper"
            )

    if executor == "binance_testnet":
        binance_api_key_testnet = _required_env(
            "BINANCE_API_KEY_TESTNET"
        )
        binance_api_secret_testnet = _required_env(
            "BINANCE_API_SECRET_TESTNET"
        )
    else:
        binance_api_key_testnet = os.getenv(
            "BINANCE_API_KEY_TESTNET"
        )
        binance_api_secret_testnet = os.getenv(
            "BINANCE_API_SECRET_TESTNET"
        )

    if executor == "binance_production":
        binance_api_key_production = _required_env(
            "BINANCE_API_KEY_PRODUCTION"
        )
        binance_api_secret_production = _required_env(
            "BINANCE_API_SECRET_PRODUCTION"
        )
    else:
        binance_api_key_production = os.getenv(
            "BINANCE_API_KEY_PRODUCTION"
        )
        binance_api_secret_production = os.getenv(
            "BINANCE_API_SECRET_PRODUCTION"
        )

    if executor == "paper":
        paper_initial_base_balance = _decimal_env(
            "PAPER_INITIAL_BASE_BALANCE"
        )
        paper_initial_quote_balance = _decimal_env(
            "PAPER_INITIAL_QUOTE_BALANCE"
        )
    else:
        paper_initial_base_balance = Decimal("0")
        paper_initial_quote_balance = Decimal("0")

    replay_delay_seconds = (
        float(
            os.getenv("REPLAY_DELAY_SECONDS")
            or "0"
        )
        if mode == "replay"
        else 0.0
    )

    return RuntimeConfig(
        mode=mode,
        instrument=InstrumentConfig(
            symbol=_required_env("SYMBOL"),
            base_asset=_required_env("BASE_ASSET"),
            quote_asset=_required_env("QUOTE_ASSET"),
            interval=_required_env("INTERVAL"),
        ),
        live=LiveConfig(
            exchange=live_exchange,
            environment=live_environment,
            mapper=live_mapper,
        ),
        replay=ReplayConfig(
            file_path=replay_file_path,
            mapper=replay_mapper,
            initial_date=replay_initial_date,
            final_date=replay_final_date,
            delay_seconds=replay_delay_seconds,
        ),
        executor=ExecutorConfig(
            executor=executor,
            paper_initial_base_balance=(
                paper_initial_base_balance
            ),
            paper_initial_quote_balance=(
                paper_initial_quote_balance
            ),
            binance_api_key_testnet=(
                binance_api_key_testnet
            ),
            binance_api_secret_testnet=(
                binance_api_secret_testnet
            ),
            binance_api_key_production=(
                binance_api_key_production
            ),
            binance_api_secret_production=(
                binance_api_secret_production
            ),
        ),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(f"{name} is required")

    return value.strip()


def _decimal_env(
    name: str,
    default: str = "0",
) -> Decimal:
    value = os.getenv(name)

    if value is None or not value.strip():
        value = default

    return Decimal(value)


def _project_path(value: str) -> str:
    path = Path(value)

    if path.is_absolute():
        return str(path)

    return str(
        (PROJECT_ROOT / path).resolve()
    )
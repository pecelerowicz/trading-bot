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

    mode = os.getenv("RUNTIME_MODE")

    live_exchange = os.getenv("LIVE_EXCHANGE")
    live_environment = os.getenv("LIVE_ENVIRONMENT")
    live_mapper = os.getenv("LIVE_MAPPER")

    replay_file_path = os.getenv("REPLAY_FILE_PATH")
    replay_mapper = os.getenv("REPLAY_MAPPER")
    replay_initial_date = os.getenv("REPLAY_INITIAL_DATE")
    replay_final_date = os.getenv("REPLAY_FINAL_DATE")

    executor = os.getenv("EXECUTOR")

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

    if mode == "live":
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
            executor == "binance_testnet"
            and live_environment != "testnet"
        ):
            raise ValueError(
                "binance_testnet executor requires "
                "LIVE_ENVIRONMENT=testnet"
            )

        if (
            executor == "binance_production"
            and live_environment != "production"
        ):
            raise ValueError(
                "binance_production executor requires "
                "LIVE_ENVIRONMENT=production"
            )

    if mode == "replay":
        if replay_file_path is None:
            raise ValueError(
                "REPLAY_FILE_PATH is required in replay mode"
            )

        if replay_mapper != "binance_rest":
            raise ValueError(
                f"Unsupported REPLAY_MAPPER: "
                f"{replay_mapper}"
            )

        if replay_initial_date is None:
            raise ValueError(
                "REPLAY_INITIAL_DATE is required "
                "in replay mode"
            )

        if replay_final_date is None:
            raise ValueError(
                "REPLAY_FINAL_DATE is required "
                "in replay mode"
            )

        if executor != "paper":
            raise ValueError(
                "Replay mode requires EXECUTOR=paper"
            )

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
            mapper=live_mapper,
        ),
        replay=ReplayConfig(
            file_path=replay_file_path,
            mapper=replay_mapper,
            initial_date=replay_initial_date,
            final_date=replay_final_date,
            delay_seconds=float(
                os.getenv("REPLAY_DELAY_SECONDS") or "0"
            ),
        ),
        executor=ExecutorConfig(
            executor=executor,
            paper_initial_base_balance=Decimal(
                os.getenv(
                    "PAPER_INITIAL_BASE_BALANCE",
                    "0",
                )
            ),
            paper_initial_quote_balance=Decimal(
                os.getenv(
                    "PAPER_INITIAL_QUOTE_BALANCE",
                    "0",
                )
            ),
            binance_api_key_testnet=os.getenv(
                "BINANCE_API_KEY_TESTNET"
            ),
            binance_api_secret_testnet=os.getenv(
                "BINANCE_API_SECRET_TESTNET"
            ),
            binance_api_key_production=os.getenv(
                "BINANCE_API_KEY_PRODUCTION"
            ),
            binance_api_secret_production=os.getenv(
                "BINANCE_API_SECRET_PRODUCTION"
            ),
        ),
    )
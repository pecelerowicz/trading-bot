import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from trading_bot.config.models import (
    ExchangeExecutorConfig,
    HistoricalDataConfig,
    InstrumentConfig,
    LiveSourceConfig,
    PaperExecutorConfig,
    ReplaySourceConfig,
    RuntimeConfig,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_runtime_config() -> RuntimeConfig:
    load_dotenv()

    runtime_mode = _get_required_env_var("RUNTIME_MODE")
    executor_type = _get_required_env_var("EXECUTOR")

    if runtime_mode not in {"live", "replay"}:
        raise ValueError(
            f"Unsupported RUNTIME_MODE: {runtime_mode}"
        )

    if executor_type not in {"paper", "exchange"}:
        raise ValueError(
            f"Unsupported EXECUTOR: {executor_type}"
        )

    instrument = InstrumentConfig(
        symbol=_get_required_env_var("SYMBOL"),
        base_asset=_get_required_env_var("BASE_ASSET"),
        quote_asset=_get_required_env_var("QUOTE_ASSET"),
        interval=_get_required_env_var("INTERVAL"),
    )

    if runtime_mode == "live":
        source_config = _load_live_source_config()
    else:
        source_config = _load_replay_source_config()

        if executor_type != "paper":
            raise ValueError(
                "RUNTIME_MODE=replay requires EXECUTOR=paper"
            )

    if executor_type == "paper":
        executor_config = _load_paper_executor_config()
    else:
        executor_config = _load_exchange_executor_config()

    return RuntimeConfig(
        instrument=instrument,
        source_config=source_config,
        executor_config=executor_config,
    )


def _load_live_source_config() -> LiveSourceConfig:
    exchange = _get_required_env_var("LIVE_EXCHANGE")
    environment = _get_required_env_var("LIVE_ENVIRONMENT")
    mapper = _get_required_env_var("LIVE_MAPPER")

    if environment not in {"testnet", "production"}:
        raise ValueError(
            f"Unsupported LIVE_ENVIRONMENT: {environment}"
        )

    return LiveSourceConfig(
        exchange=exchange,
        environment=environment,
        mapper=mapper,
    )


def _load_replay_source_config() -> ReplaySourceConfig:
    historical_data = HistoricalDataConfig(
        file_path=_project_path(
            _get_required_env_var("REPLAY_FILE_PATH")
        ),
        mapper=_get_required_env_var("REPLAY_MAPPER"),
        initial_date=_get_required_env_var(
            "REPLAY_INITIAL_DATE"
        ),
        final_date=_get_required_env_var(
            "REPLAY_FINAL_DATE"
        ),
    )

    return ReplaySourceConfig(
        historical_data=historical_data,
        delay_seconds=float(
            os.getenv("REPLAY_DELAY_SECONDS") or "0"
        ),
    )


def _load_paper_executor_config() -> PaperExecutorConfig:
    return PaperExecutorConfig(
        initial_base_balance=_get_decimal_env_var(
            "PAPER_INITIAL_BASE_BALANCE"
        ),
        initial_quote_balance=_get_decimal_env_var(
            "PAPER_INITIAL_QUOTE_BALANCE"
        ),
    )


def _load_exchange_executor_config() -> ExchangeExecutorConfig:
    exchange = _get_required_env_var("EXECUTOR_EXCHANGE")
    environment = _get_required_env_var("EXECUTOR_ENVIRONMENT")

    if environment not in {"testnet", "production"}:
        raise ValueError(
            f"Unsupported EXECUTOR_ENVIRONMENT: {environment}"
        )

    return ExchangeExecutorConfig(
        exchange=exchange,
        environment=environment,
    )


def _get_required_env_var(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(f"{name} is required")

    return value.strip()


def _get_decimal_env_var(
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
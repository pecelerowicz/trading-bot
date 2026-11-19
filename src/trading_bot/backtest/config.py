import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from trading_bot.config import (
    InstrumentConfig,
    PaperExecutorConfig,
    ReplaySourceConfig,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class BacktestConfig:
    instrument: InstrumentConfig
    source_config: ReplaySourceConfig
    executor_config: PaperExecutorConfig


def load_backtest_config() -> BacktestConfig:
    load_dotenv(PROJECT_ROOT / ".env.backtest")

    instrument = InstrumentConfig(
        symbol=_get_required_env_var("SYMBOL"),
        base_asset=_get_required_env_var("BASE_ASSET"),
        quote_asset=_get_required_env_var("QUOTE_ASSET"),
        interval=_get_required_env_var("INTERVAL"),
    )

    source_config = ReplaySourceConfig(
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
        delay_seconds=0.0,
    )

    executor_config = PaperExecutorConfig(
        initial_base_balance=Decimal(
            _get_required_env_var("PAPER_INITIAL_BASE_BALANCE")
        ),
        initial_quote_balance=Decimal(
            _get_required_env_var("PAPER_INITIAL_QUOTE_BALANCE")
        ),
    )

    return BacktestConfig(
        instrument=instrument,
        source_config=source_config,
        executor_config=executor_config,
    )


def _get_required_env_var(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(f"{name} is required")

    return value.strip()


def _project_path(value: str) -> str:
    path = Path(value)

    if path.is_absolute():
        return str(path)

    return str(
        (PROJECT_ROOT / path).resolve()
    )
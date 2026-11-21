import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from trading_bot.config.models import (
    BacktestConfig,
    HistoricalDataConfig,
    InstrumentConfig,
    PaperExecutorConfig,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_backtest_config() -> BacktestConfig:
    load_dotenv(PROJECT_ROOT / ".env.backtest")

    instrument = InstrumentConfig(
        symbol=_get_required_env_var("SYMBOL"),
        base_asset=_get_required_env_var("BASE_ASSET"),
        quote_asset=_get_required_env_var("QUOTE_ASSET"),
        interval=_get_required_env_var("INTERVAL"),
    )

    historical_data = HistoricalDataConfig(
        file_path=_project_path(
            _get_required_env_var("HISTORICAL_FILE_PATH")
        ),
        mapper=_get_required_env_var("HISTORICAL_MAPPER"),
        initial_date=_get_required_env_var(
            "HISTORICAL_INITIAL_DATE"
        ),
        final_date=_get_required_env_var(
            "HISTORICAL_FINAL_DATE"
        ),
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
        historical_data=historical_data,
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
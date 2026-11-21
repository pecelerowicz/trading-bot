from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class InstrumentConfig:
    symbol: str
    base_asset: str
    quote_asset: str
    interval: str


@dataclass(frozen=True)
class HistoricalDataConfig:
    file_path: str
    mapper: str
    initial_date: str
    final_date: str


@dataclass(frozen=True)
class LiveSourceConfig:
    exchange: str
    environment: str
    mapper: str


@dataclass(frozen=True)
class ReplaySourceConfig:
    historical_data: HistoricalDataConfig
    delay_seconds: float = 0.0


@dataclass(frozen=True)
class PaperExecutorConfig:
    initial_base_balance: Decimal
    initial_quote_balance: Decimal


@dataclass(frozen=True)
class ExchangeExecutorConfig:
    exchange: str
    environment: str


@dataclass(frozen=True)
class RuntimeConfig:
    instrument: InstrumentConfig
    source_config: LiveSourceConfig | ReplaySourceConfig
    executor_config: PaperExecutorConfig | ExchangeExecutorConfig


@dataclass(frozen=True)
class BacktestConfig:
    instrument: InstrumentConfig
    historical_data: HistoricalDataConfig
    executor_config: PaperExecutorConfig
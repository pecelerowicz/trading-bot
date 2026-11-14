from decimal import Decimal

from trading_bot.adapters.binance_executor import BinanceExecutor
from trading_bot.adapters.binance_market_data_source import (
    BinanceMarketDataSource,
)
from trading_bot.adapters.binance_rest_kline_mapper import (
    map_rest_kline,
)
from trading_bot.adapters.historical_kline_loader import (
    load_historical_klines,
)
from trading_bot.adapters.paper_executor import PaperExecutor
from trading_bot.adapters.replay_market_data_source import (
    ReplayMarketDataSource,
)
from trading_bot.config import (
    ExchangeExecutorConfig,
    InstrumentConfig,
    LiveSourceConfig,
    PaperExecutorConfig,
    ReplaySourceConfig,
)
from trading_bot.models.account import AccountSnapshot, AssetBalance
from trading_bot.models.instrument import Instrument
from trading_bot.ports.executor import Executor
from trading_bot.ports.market_data_source import MarketDataSource
from trading_bot.trading.debug_logger import TradingDebugLogger


async def build_live_market_data_source(
    source_config: LiveSourceConfig,
    instrument_config: InstrumentConfig,
) -> MarketDataSource:
    if source_config.exchange == "binance":
        if source_config.mapper != "binance_websocket":
            raise NotImplementedError(
                f"Live mapper '{source_config.mapper}' "
                "is not implemented"
            )

        return await BinanceMarketDataSource.create(
            environment=source_config.environment,
            symbol=instrument_config.symbol,
            interval=instrument_config.interval,
        )

    # TODO: Add another exchange implementation here, e.g. Bybit.
    raise NotImplementedError(
        f"Live market data for exchange "
        f"'{source_config.exchange}' is not implemented"
    )


def build_replay_market_data_source(
    source_config: ReplaySourceConfig,
) -> ReplayMarketDataSource:
    if source_config.mapper != "binance_rest":
        raise NotImplementedError(
            f"Replay mapper '{source_config.mapper}' "
            "is not implemented"
        )

    klines = load_historical_klines(
        file_path=source_config.file_path,
        mapper=map_rest_kline,
        initial_date=source_config.initial_date,
        final_date=source_config.final_date,
    )

    return ReplayMarketDataSource(
        klines=klines,
        delay_seconds=source_config.delay_seconds,
    )


async def build_executor(
    executor_config: PaperExecutorConfig | ExchangeExecutorConfig,
    instrument: Instrument,
    logger: TradingDebugLogger,
) -> Executor:
    if isinstance(executor_config, PaperExecutorConfig):
        initial_account = AccountSnapshot(
            balances=(
                AssetBalance(
                    asset=instrument.base_asset,
                    free=executor_config.initial_base_balance,
                    locked=Decimal("0"),
                ),
                AssetBalance(
                    asset=instrument.quote_asset,
                    free=executor_config.initial_quote_balance,
                    locked=Decimal("0"),
                ),
            )
        )

        return PaperExecutor(
            logger=logger,
            instrument=instrument,
            initial_account=initial_account,
        )

    if executor_config.exchange == "binance":
        return await BinanceExecutor.create(
            environment=executor_config.environment,
            instrument=instrument,
        )

    # TODO: Add another exchange implementation here, e.g. Bybit.
    raise NotImplementedError(
        f"Execution for exchange "
        f"'{executor_config.exchange}' is not implemented"
    )
from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    symbol: str
    base_asset: str
    quote_asset: str

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Instrument symbol cannot be empty")

        if not self.base_asset:
            raise ValueError("Base asset cannot be empty")

        if not self.quote_asset:
            raise ValueError("Quote asset cannot be empty")

        if self.base_asset == self.quote_asset:
            raise ValueError("Base asset and quote asset must be different")
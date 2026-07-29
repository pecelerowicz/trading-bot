from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AssetBalance:
    asset: str
    free: Decimal
    locked: Decimal

    @property
    def total(self) -> Decimal:
        return self.free + self.locked


@dataclass(frozen=True)
class AccountSnapshot:
    balances: tuple[AssetBalance, ...]

    def get_balance(self, asset: str) -> AssetBalance:
        for balance in self.balances:
            if balance.asset == asset:
                return balance

        return AssetBalance(
            asset=asset,
            free=Decimal("0"),
            locked=Decimal("0"),
        )

    def has_free_balance(self, asset: str, amount: Decimal) -> bool:
        return self.get_balance(asset).free >= amount
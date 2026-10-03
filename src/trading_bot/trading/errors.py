class UnexpectedOrderStateError(RuntimeError):
    pass


class MarketOrderNotFullyFilledError(RuntimeError):
    pass


class OrderCancellationNotCompletedError(RuntimeError):
    pass


class StrategySignalConflictError(RuntimeError):
    pass
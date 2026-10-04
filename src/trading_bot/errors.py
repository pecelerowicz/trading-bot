class InvalidOrderRequestError(ValueError):
    pass


class OrderRejectedError(Exception):
    pass


class OrderPlacementOutcomeUnknownError(Exception):
    pass


class UnexpectedOrderStateError(RuntimeError):
    pass


class MarketOrderNotFullyFilledError(RuntimeError):
    pass


class OrderCancellationNotCompletedError(RuntimeError):
    pass


class StrategySignalConflictError(RuntimeError):
    pass
class InvalidOrderRequestError(ValueError):
    pass


class ExecutorError(Exception):
    pass


class OrderPlacementRejectedError(ExecutorError):
    pass


class OrderPlacementOutcomeUnknownError(ExecutorError):
    pass


class OrderNotFoundError(ExecutorError):
    pass


class OrderRetrievalError(ExecutorError):
    pass


class OrderCancellationRejectedError(ExecutorError):
    pass


class OrderCancellationOutcomeUnknownError(ExecutorError):
    pass


class UnexpectedOrderStateError(RuntimeError):
    pass


class MarketOrderNotFullyFilledError(RuntimeError):
    pass


class OrderCancellationNotCompletedError(RuntimeError):
    pass


class StrategySignalConflictError(RuntimeError):
    pass
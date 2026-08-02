class TradingBotError(RuntimeError):
    pass


class RecoveryRequiredError(TradingBotError):
    pass


class ExecutorError(RecoveryRequiredError):
    pass


class OrderPlacementOutcomeUnknownError(ExecutorError):
    pass


class OrderCancellationOutcomeUnknownError(ExecutorError):
    pass


class OrderSynchronizationError(ExecutorError):
    pass


class AccountSnapshotError(ExecutorError):
    pass


class InvalidExecutorResponseError(ExecutorError):
    pass


class UnexpectedOrderStateError(RecoveryRequiredError):
    pass


class OrderNotAcceptedError(UnexpectedOrderStateError):
    pass


class MarketOrderNotAcceptedError(OrderNotAcceptedError):
    pass


class LimitOrderNotAcceptedError(OrderNotAcceptedError):
    pass


class MarketOrderNotFullyFilledError(UnexpectedOrderStateError):
    pass


class OrderCancellationNotCompletedError(UnexpectedOrderStateError):
    pass


class StrategySignalConflictError(RecoveryRequiredError):
    pass
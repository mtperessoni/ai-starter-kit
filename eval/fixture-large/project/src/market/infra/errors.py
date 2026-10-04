"""Error types shared by every rule (CAT-*, CRT-*, INV-*, CHK-*, PAY-*)."""


class MarketError(Exception):
    code = "error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(MarketError):
    code = "not_found"


class ValidationError(MarketError):
    code = "invalid"


class OutOfStockError(MarketError):
    code = "out_of_stock"

    def __init__(self, message: str = "", skus: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.skus = tuple(skus)


class PolicyError(MarketError):
    code = "policy"

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

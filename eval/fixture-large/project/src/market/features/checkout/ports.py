"""CHK-03, CHK-04, LOY-04: the port through which checkout reaches loyalty without importing it."""
from decimal import Decimal
from typing import Protocol

from market.infra.errors import PolicyError


class LoyaltyPort(Protocol):
    def redemption_value(self, customer_id: str, points: int, merchandise_total: Decimal) -> Decimal:
        """Money value of the points a customer wants to redeem on this merchandise total."""


class _NullPort:
    """Default port when no loyalty feature is wired: only a redemption of zero points is allowed."""

    def redemption_value(self, customer_id: str, points: int, merchandise_total: Decimal) -> Decimal:
        if points == 0:
            return Decimal("0.00")
        raise PolicyError("loyalty_unavailable")


_NULL_PORT = _NullPort()
_port: LoyaltyPort | None = None


def set_loyalty_port(port: LoyaltyPort | None) -> None:
    """Wire the loyalty implementation; None restores the null port (done by api.py at import)."""
    global _port
    _port = port


def get_loyalty_port() -> LoyaltyPort:
    """The wired port, or the null port that refuses any redemption above zero points."""
    return _port if _port is not None else _NULL_PORT

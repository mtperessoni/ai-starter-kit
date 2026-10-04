"""Decimal helpers: half-up cents and proportional allocation (PRC-04)."""
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

_CENT = Decimal("0.01")


def D(value: "str | int | Decimal") -> Decimal:
    return Decimal(str(value))


def q2(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def pct(amount: Decimal, percent: Decimal) -> Decimal:
    return amount * percent / Decimal(100)


def allocate(amount: Decimal, weights: Sequence[Decimal]) -> list[Decimal]:
    """Split amount in proportion to weights; the last positive weight takes the remainder."""
    pieces = [Decimal("0.00") for _ in weights]
    total = sum(weights, Decimal("0"))
    if total <= 0:
        return pieces
    last = max(i for i, w in enumerate(weights) if w > 0)
    given = Decimal("0.00")
    for i, weight in enumerate(weights[:last]):
        pieces[i] = q2(amount * weight / total)
        given += pieces[i]
    pieces[last] = q2(amount) - given
    return pieces

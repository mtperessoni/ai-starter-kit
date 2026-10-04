"""LOY-05, LOY-06: points lots, FIFO spending, expiry and claw-back."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from market.infra import clock, config, ids
from market.infra.errors import PolicyError, ValidationError
from market.infra.repositories import repo

_REPO = "points_lots"


@dataclass
class PointsLot:
    lot_id: str
    customer_id: str
    points: int
    remaining: int
    earned_at: datetime
    reason: str = ""


def _expires_at(lot: PointsLot) -> datetime:
    return lot.earned_at + timedelta(days=config.get("loyalty.expiry_days"))


def _is_expired(lot: PointsLot) -> bool:
    return clock.now() >= _expires_at(lot)


def _lots(customer_id: str) -> list[PointsLot]:
    """Lots of a customer, oldest first (the order points are spent in)."""
    mine = [lot for lot in repo(_REPO).all() if lot.customer_id == customer_id]
    return sorted(mine, key=lambda lot: (lot.earned_at, lot.lot_id))


def _live_lots(customer_id: str) -> list[PointsLot]:
    return [lot for lot in _lots(customer_id) if lot.remaining > 0 and not _is_expired(lot)]


def add_points(customer_id: str, points: int, reason: str) -> None:
    """Add a lot of points earned now; it expires after the configured days (LOY-05).

    The reason is kept on the lot for audit: order id, grant, redeem_refund.
    """
    if points <= 0:
        raise ValidationError("points to add must be positive")
    if not reason.strip():
        raise ValidationError("a reason is required")
    lot = PointsLot(ids.next_id("LOT"), customer_id, points, points, clock.now(), reason)
    repo(_REPO).add(lot.lot_id, lot)


def balance(customer_id: str) -> int:
    """Points that can still be spent: remaining points of lots that have not expired."""
    return sum(lot.remaining for lot in _live_lots(customer_id))


def spend(customer_id: str, points: int) -> None:
    """Spend points oldest lot first; refuses when the balance is short and changes nothing.

    A customer with lots of 300 (older) and 400 who spends 500 is left with 0 in the first lot and
    200 in the second (LOY-05).
    """
    if points <= 0:
        raise ValidationError("points to spend must be positive")
    if points > balance(customer_id):
        raise PolicyError("insufficient_points")
    left = points
    for lot in _live_lots(customer_id):
        taken = min(lot.remaining, left)
        lot.remaining -= taken
        left -= taken
        if left == 0:
            break


def claw_back(customer_id: str, points: int) -> int:
    """Take points back after a cancellation or a return, never below a zero balance (LOY-06).

    Returns how many points were actually removed. The newest lots are emptied first, because they
    are the points the order just earned.
    """
    if points < 0:
        raise ValidationError("points to claw back cannot be negative")
    removed = 0
    for lot in reversed(_live_lots(customer_id)):
        if removed == points:
            break
        taken = min(lot.remaining, points - removed)
        lot.remaining -= taken
        removed += taken
    return removed


def expire_lots(customer_id: str) -> int:
    """Zero the lots past their expiry and return how many points that removed (LOY-05)."""
    expired = 0
    for lot in _lots(customer_id):
        if lot.remaining > 0 and _is_expired(lot):
            expired += lot.remaining
            lot.remaining = 0
    return expired


def lots_of(customer_id: str) -> list[PointsLot]:
    """Lots that still hold points, oldest first, expired ones left out."""
    return _live_lots(customer_id)


def expiring_points(customer_id: str, within_days: int) -> int:
    """Points that will expire within the next `within_days` days (LOY-05).

    A lot earned 350 days ago expires in 15 days, so it counts for within_days=30.
    """
    if within_days < 0:
        raise ValidationError("days cannot be negative")
    horizon = clock.now() + timedelta(days=within_days)
    return sum(lot.remaining for lot in _live_lots(customer_id) if _expires_at(lot) <= horizon)


def lifetime_points(customer_id: str) -> int:
    """Points ever added to the customer, expired and spent ones included."""
    return sum(lot.points for lot in _lots(customer_id))


def points_summary(customer_id: str) -> dict[str, int]:
    """Balance, points expiring in the next 30 days and lifetime points in one dict.

        {"balance": 500, "expiring_30_days": 0, "lifetime": 620}
    """
    return {
        "balance": balance(customer_id),
        "expiring_30_days": expiring_points(customer_id, 30),
        "lifetime": lifetime_points(customer_id),
    }

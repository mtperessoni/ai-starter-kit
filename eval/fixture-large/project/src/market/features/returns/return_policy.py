"""RET-01, RET-02, RET-05: who can return what, and until when."""
from collections.abc import Sequence
from datetime import date, timedelta

from market.features.catalog.category_rules import is_returnable
from market.features.checkout.order_models import DELIVERED, PARTIALLY_REFUNDED, Order
from market.infra import config
from market.infra.errors import PolicyError, ValidationError

REASONS = ("defective", "wrong_item", "changed_mind", "other")
_ELIGIBLE_STATUSES = (DELIVERED, PARTIALLY_REFUNDED)


def merge_items(items: Sequence[tuple[str, int]]) -> dict[str, int]:
    """Sum repeated SKUs; every quantity must be a positive whole number."""
    merged: dict[str, int] = {}
    for sku, qty in items:
        if qty < 1:
            raise ValidationError(f"quantity of {sku} must be at least 1")
        merged[sku] = merged.get(sku, 0) + qty
    return merged


def _check_window(order: Order, today: date) -> None:
    if order.delivered_at is None:
        raise PolicyError("order_not_delivered")
    days = (today - order.delivered_at.date()).days
    if days > config.get("returns.window_days"):
        raise PolicyError("return_window_closed")


def check_eligibility(order: Order, items: Sequence[tuple[str, int]], reason: str, today: date) -> None:
    """Raise unless the return can go ahead.

    ValidationError: unknown reason, empty list, a SKU not in the order, or more units than were
    bought minus the ones already returned (RET-05).
    PolicyError: the order is not delivered or partially refunded, the 30-day window after delivery
    is over (RET-01), or a line is a gift card or grocery (RET-02).

    A delivery on day 0 can be returned through day 30 and is refused on day 31.
    """
    if reason not in REASONS:
        raise ValidationError(f"reason must be one of {', '.join(REASONS)}")
    wanted = merge_items(items)
    if not wanted:
        raise ValidationError("a return needs at least one item")
    if order.status not in _ELIGIBLE_STATUSES:
        raise PolicyError(f"order_{order.status}")
    _check_window(order, today)
    categories = {line.sku: line.category for line in order.lines}
    for sku, qty in wanted.items():
        if sku not in categories:
            raise ValidationError(f"{sku} is not in the order")
        if not is_returnable(categories[sku]):
            raise PolicyError("not_returnable")
        if qty > order.units_left_to_return(sku):
            raise ValidationError(f"only {order.units_left_to_return(sku)} units of {sku} can still be returned")


def return_deadline(order: Order) -> date | None:
    """Last day a return can start, or None when the order has not been delivered (RET-01)."""
    if order.delivered_at is None:
        return None
    return order.delivered_at.date() + timedelta(days=config.get("returns.window_days"))


def returnable_units(order: Order) -> dict[str, int]:
    """Units still returnable per SKU: bought minus returned, gift cards and grocery left out (RET-02, RET-05)."""
    left: dict[str, int] = {}
    for line in order.lines:
        if is_returnable(line.category) and order.units_left_to_return(line.sku) > 0:
            left[line.sku] = order.units_left_to_return(line.sku)
    return left


def return_window_open(order: Order, today: date) -> bool:
    """True when a return could still start today: delivered, and the deadline has not passed (RET-01)."""
    deadline = return_deadline(order)
    return deadline is not None and today <= deadline

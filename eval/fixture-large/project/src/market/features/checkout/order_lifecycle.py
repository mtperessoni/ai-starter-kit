"""CHK-08, CHK-09, PRM-04, INV-05: order status moves, cancellation and applied returns."""
from collections.abc import Sequence
from datetime import date

from market.features.catalog.category_rules import is_stock_tracked
from market.features.checkout.order_models import (CANCELLED, DELIVERED, PAID, PARTIALLY_REFUNDED,
                                                    REFUNDED, SHIPPED, Order, merchandise_points_base)
from market.features.inventory.stock_store import add_stock
from market.features.payments.payment_service import get_payment, refund
from market.features.promotions.promotion_usage import release_uses
from market.infra import clock, events
from market.infra.errors import PolicyError, ValidationError
from market.infra.repositories import repo

_ORDERS = "orders"
_RETURNABLE_STATUSES = (DELIVERED, PARTIALLY_REFUNDED)


def get_order(order_id: str) -> Order:
    return repo(_ORDERS).get(order_id)


def _require_status(order: Order, allowed: tuple[str, ...], action: str) -> None:
    if order.status not in allowed:
        raise PolicyError(f"cannot_{action}_{order.status}")


def mark_shipped(order_id: str) -> Order:
    """paid -> shipped (CHK-08)."""
    order = get_order(order_id)
    _require_status(order, (PAID,), "ship")
    order.status = SHIPPED
    order.shipped_at = clock.now()
    return order


def mark_delivered(order_id: str) -> Order:
    """shipped -> delivered (CHK-08); the return window starts here (RET-01)."""
    order = get_order(order_id)
    _require_status(order, (SHIPPED,), "deliver")
    order.status = DELIVERED
    order.delivered_at = clock.now()
    return order


def _give_back_uses(order_id: str) -> None:
    """Free the coupon uses of a paid order. release_uses frees held uses only, and a paid order
    has committed ones, so those are flipped here (PRM-04, CHK-09)."""
    release_uses(order_id)
    use = repo("promo_uses").find(order_id)
    if use is not None and use.status == "committed":
        use.status = "released"


def _restock(order: Order) -> None:
    for line in order.lines:
        if is_stock_tracked(line.category):
            add_stock(line.sku, line.qty)


def cancel_order(order_id: str) -> Order:
    """Cancel a paid order that has not shipped (CHK-09).

    Refunds what was captured, puts the stock back, gives the coupon uses back and publishes
    order.cancelled so loyalty takes back earned points and returns redeemed ones (LOY-06).
    """
    order = get_order(order_id)
    _require_status(order, (PAID,), "cancel")
    if order.payment_id is not None:
        payment = get_payment(order.payment_id)
        if payment.refundable > 0:
            refund(order.payment_id, payment.refundable)
    _restock(order)
    _give_back_uses(order_id)
    order.status = CANCELLED
    events.publish(
        "order.cancelled", order_id=order_id, customer_id=order.customer_id,
        points_base=merchandise_points_base(order.lines), points_redeemed=order.points_redeemed,
    )
    return order


def apply_return(order_id: str, items: Sequence[tuple[str, int]]) -> Order:
    """Record returned units on a delivered order and lower its status (CHK-08, RET-07).

    The status becomes partially_refunded while units remain and refunded when every unit of
    every line has been returned. The caller (returns) has already checked eligibility; this
    guards the counters so they can never exceed the units bought.
    """
    order = get_order(order_id)
    _require_status(order, _RETURNABLE_STATUSES, "return")
    wanted: dict[str, int] = {}
    for sku, qty in items:
        wanted[sku] = wanted.get(sku, 0) + qty
    for sku, qty in wanted.items():
        if qty < 1 or qty > order.units_left_to_return(sku):
            raise ValidationError(f"cannot return {qty} of {sku}")
    for sku, qty in wanted.items():
        order.returned_units[sku] = order.returned_units.get(sku, 0) + qty
    everything = all(order.units_left_to_return(line.sku) == 0 for line in order.lines)
    order.status = REFUNDED if everything else PARTIALLY_REFUNDED
    return order


def list_orders(customer_id: str | None = None, status: str | None = None) -> list[Order]:
    """Orders in the order they were placed, optionally for one customer or one status."""
    return [
        order for order in repo(_ORDERS).all()
        if (customer_id is None or order.customer_id == customer_id)
        and (status is None or order.status == status)
    ]


def can_cancel(order: Order) -> bool:
    """True while the order is paid and not yet shipped (CHK-09)."""
    return order.status == PAID


def can_return(order: Order) -> bool:
    """True when the order is delivered or partially refunded and has units left (CHK-08)."""
    return order.status in _RETURNABLE_STATUSES and any(
        order.units_left_to_return(line.sku) > 0 for line in order.lines
    )


def awaiting_shipment() -> list[Order]:
    """Paid orders that have not shipped yet, oldest first: the warehouse work list (CHK-08)."""
    return sorted(list_orders(status=PAID), key=lambda order: order.paid_at or order.created_at)


def days_since(order: Order, today: date) -> int:
    """Whole days between the order being placed and `today`."""
    return (today - order.created_at.date()).days

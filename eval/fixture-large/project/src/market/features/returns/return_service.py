"""RET-05, RET-06, RET-07: request a return, refund, restock and tell loyalty."""
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal

from market.features.catalog.category_rules import is_digital, is_stock_tracked
from market.features.checkout.order_lifecycle import apply_return, get_order
from market.features.checkout.order_models import Order
from market.features.inventory.stock_store import add_stock
from market.features.payments.payment_service import get_payment, refund
from market.features.returns.refund_calculator import compute_refund, prorate
from market.features.returns.return_models import STATUS_COMPLETED, RefundBreakdown, ReturnRequest
from market.features.returns.return_policy import check_eligibility, merge_items
from market.infra import clock, events, ids
from market.infra.repositories import repo

_REPO = "returns"
ZERO = Decimal("0.00")


def get_return(return_id: str) -> ReturnRequest:
    return repo(_REPO).get(return_id)


def _cap_to_payment(order: Order, refund_breakdown: RefundBreakdown) -> RefundBreakdown:
    """Never refund more than the payment still holds; a loyalty discount makes the sum of
    prorated lines larger than what was paid (PAY-07, PAY-08)."""
    if order.payment_id is None:
        return replace(refund_breakdown, total=ZERO)
    left = get_payment(order.payment_id).refundable
    if refund_breakdown.total <= left:
        return refund_breakdown
    return replace(refund_breakdown, total=left)


def _restock(order: Order, wanted: dict[str, int], reason: str) -> None:
    """Returned goods go back to stock unless they are defective (RET-06)."""
    if reason == "defective":
        return
    for line in order.lines:
        if line.sku in wanted and is_stock_tracked(line.category):
            add_stock(line.sku, wanted[line.sku])


def _points_base_returned(order: Order, wanted: dict[str, int]) -> Decimal:
    return sum(
        (prorate(line.line_total, line.qty, wanted[line.sku])
         for line in order.lines if line.sku in wanted and not is_digital(line.category)),
        ZERO,
    )


def request_return(order_id: str, items: Sequence[tuple[str, int]], reason: str) -> ReturnRequest:
    """Run a return end to end and complete it (RET-07).

    1. check eligibility (window, categories, quantities, reason);
    2. compute the refund breakdown and cap it to what the payment still holds;
    3. refund the payment;
    4. put returned goods back in stock unless the reason is defective (RET-06);
    5. lower the order status through checkout (partially_refunded or refunded);
    6. publish return.completed so loyalty takes back points and notifications tells the customer.
    """
    order = get_order(order_id)
    check_eligibility(order, items, reason, clock.today())
    wanted = merge_items(items)
    breakdown = _cap_to_payment(order, compute_refund(order, items, reason))
    if breakdown.total > 0:
        refund(order.payment_id, breakdown.total)
    _restock(order, wanted, reason)
    apply_return(order_id, list(wanted.items()))
    request = ReturnRequest(
        return_id=ids.next_id("RET"), order_id=order_id, customer_id=order.customer_id,
        items=tuple(wanted.items()), reason=reason, status=STATUS_COMPLETED, refund=breakdown,
        created_at=clock.now(),
    )
    repo(_REPO).add(request.return_id, request)
    events.publish(
        "return.completed", return_id=request.return_id, order_id=order_id,
        customer_id=order.customer_id, points_base_returned=_points_base_returned(order, wanted),
        refund_total=breakdown.total,
    )
    return request


def list_returns(order_id: str | None = None) -> list[ReturnRequest]:
    """Completed returns in the order they happened, optionally for one order."""
    return [r for r in repo(_REPO).all() if order_id is None or r.order_id == order_id]


def total_returned_value(order_id: str) -> Decimal:
    """Money refunded through returns of an order."""
    return sum((r.refund.total for r in list_returns(order_id)), ZERO)


def refund_summary(request: ReturnRequest) -> str:
    """One line describing what a return refunded.

        RET-0001 129.60 (merchandise 120.00, tax 9.60, shipping 0.00)
    """
    refund_part = request.refund
    return (f"{request.return_id} {refund_part.total} (merchandise {refund_part.merchandise}, "
            f"tax {refund_part.tax}, shipping {refund_part.shipping})")

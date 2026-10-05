"""RET-03, RET-04: the money a return refunds, prorated per unit."""
from collections.abc import Sequence
from decimal import Decimal

from market.features.checkout.order_models import Order, OrderLine
from market.features.returns.return_models import RefundBreakdown
from market.features.returns.return_policy import merge_items
from market.infra.money import q2

ZERO = Decimal("0.00")
SHIPPING_REASONS = ("defective", "wrong_item")


def prorate(amount: Decimal, line_qty: int, units: int) -> Decimal:
    """Amount of `units` out of `line_qty`, rounded half up to cents (RET-03).

    A 96.00 line of 3 units gives 32.00 for one unit and 64.00 for two; 100.00 over 3 units gives
    33.33 per unit.
    """
    return q2(amount / line_qty * units)


def _line_for(order: Order, sku: str) -> OrderLine:
    return next(line for line in order.lines if line.sku == sku)


def _returns_everything(order: Order, wanted: dict[str, int]) -> bool:
    """True when, counting earlier returns, every unit of every line has come back (RET-04)."""
    return all(
        order.returned_units.get(line.sku, 0) + wanted.get(line.sku, 0) >= order.units_bought(line.sku)
        for line in order.lines
    )


def compute_refund(order: Order, items: Sequence[tuple[str, int]], reason: str) -> RefundBreakdown:
    """Refund for the returned units.

    Merchandise is the line total after discounts divided by the line quantity times the units,
    and the tax of those units is prorated the same way (RET-03). Shipping is refunded only for
    reasons defective or wrong_item and only when this return brings the returned units to every
    unit of the order (RET-04). Loyalty discounts are not prorated.
    """
    wanted = merge_items(items)
    merchandise = ZERO
    tax = ZERO
    for sku, units in wanted.items():
        line = _line_for(order, sku)
        merchandise += prorate(line.line_total, line.qty, units)
        tax += prorate(line.tax, line.qty, units)
    shipping = ZERO
    if reason in SHIPPING_REASONS and _returns_everything(order, wanted):
        shipping = order.shipping
    return RefundBreakdown(merchandise, tax, shipping, merchandise + tax + shipping)

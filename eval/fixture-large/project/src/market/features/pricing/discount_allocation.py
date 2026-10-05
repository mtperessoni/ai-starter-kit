"""PRC-04, PRC-06: aggregate applied discounts per line."""
from collections.abc import Sequence
from decimal import Decimal

from market.features.promotions.promotion_models import AppliedDiscount


def line_discount_map(discounts: Sequence[AppliedDiscount]) -> dict[str, Decimal]:
    """Sum of every discount's `line_amounts` per sku, so a line total adds up exactly."""
    totals: dict[str, Decimal] = {}
    for discount in discounts:
        for sku, amount in discount.line_amounts:
            totals[sku] = totals.get(sku, Decimal("0.00")) + amount
    return totals

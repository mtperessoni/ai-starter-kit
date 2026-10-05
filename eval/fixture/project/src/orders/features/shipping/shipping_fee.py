"""SHP-01, SHP-02: the shipping fee of an order."""

from decimal import Decimal

SHIPPING_COST = Decimal("15.00")
FREE_SHIPPING_THRESHOLD = Decimal("200.00")
FREE = Decimal("0.00")


def shipping_fee(amount_after_discount: Decimal) -> Decimal:
    if amount_after_discount > FREE_SHIPPING_THRESHOLD:
        return FREE
    return SHIPPING_COST

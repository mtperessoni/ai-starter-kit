"""PRC-01, PRC-02, PRC-03, PRC-04: the discount a customer gets on a subtotal."""

from decimal import Decimal

from orders.infra.cart_models import Coupon, Customer

VIP_PERCENT = Decimal("15")
MAX_DISCOUNT_PERCENT = Decimal("30")
HUNDRED = Decimal("100")


def compute_discount(subtotal: Decimal, customer: Customer, coupon: Coupon | None = None) -> Decimal:
    percent = Decimal("0")
    if customer.vip:
        percent += VIP_PERCENT
    if coupon is not None:
        percent += coupon.percent
    discount = subtotal * percent / HUNDRED
    cap = subtotal * MAX_DISCOUNT_PERCENT / HUNDRED
    return min(discount, cap)

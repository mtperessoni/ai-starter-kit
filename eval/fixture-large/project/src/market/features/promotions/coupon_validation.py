"""PRM-02, PRM-03, PRM-04: coupon validity checks with a fixed reason order."""
from datetime import date
from decimal import Decimal

from market.features.promotions.coupon_store import find_coupon
from market.features.promotions.promotion_usage import usage_count


def check_coupon(code: str, eligible_subtotal: Decimal, customer_id: str, today: date) -> str | None:
    """Return the first failing reason, or None when the coupon is valid."""
    coupon = find_coupon(code)
    if coupon is None:
        return "unknown"
    if coupon.starts_on is not None and today < coupon.starts_on:
        return "not_started"
    if coupon.expires_on is not None and today > coupon.expires_on:
        return "expired"
    if eligible_subtotal < coupon.min_subtotal:
        return "below_minimum"
    if coupon.global_limit is not None and usage_count(coupon.code) >= coupon.global_limit:
        return "limit_reached"
    if (coupon.per_customer_limit is not None
            and usage_count(coupon.code, customer_id) >= coupon.per_customer_limit):
        return "customer_limit_reached"
    return None

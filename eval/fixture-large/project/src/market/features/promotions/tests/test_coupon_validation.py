"""Tests for coupon_validation (PRM-02, PRM-03, PRM-04: reasons in a fixed order)."""
from datetime import date
from decimal import Decimal

from market.features.promotions.coupon_store import add_coupon
from market.features.promotions.coupon_validation import check_coupon
from market.features.promotions.promotion_models import Coupon
from market.features.promotions.promotion_usage import hold_uses

TODAY = date(2026, 3, 10)


def D(value):
    return Decimal(value)


def test_valid_coupon_returns_none():
    add_coupon(Coupon("SAVE10", "percent", D("10"), min_subtotal=D("50.00")))
    assert check_coupon("save10", D("50.00"), "C-1", TODAY) is None


def test_unknown():
    assert check_coupon("NOPE", D("100"), "C-1", TODAY) == "unknown"


def test_not_started_and_expired_with_both_days_included():
    add_coupon(Coupon("WIN", "percent", D("10"), starts_on=date(2026, 3, 10), expires_on=date(2026, 3, 12)))
    assert check_coupon("WIN", D("1"), "C-1", date(2026, 3, 9)) == "not_started"
    assert check_coupon("WIN", D("1"), "C-1", date(2026, 3, 10)) is None
    assert check_coupon("WIN", D("1"), "C-1", date(2026, 3, 12)) is None
    assert check_coupon("WIN", D("1"), "C-1", date(2026, 3, 13)) == "expired"


def test_below_minimum():
    add_coupon(Coupon("MIN", "fixed", D("15"), min_subtotal=D("80.00")))
    assert check_coupon("MIN", D("79.99"), "C-1", TODAY) == "below_minimum"
    assert check_coupon("MIN", D("80.00"), "C-1", TODAY) is None


def test_global_limit_counts_every_customer():
    add_coupon(Coupon("ONCE", "percent", D("10"), global_limit=1))
    hold_uses("ORD-1", "C-2", ["ONCE"])
    assert check_coupon("ONCE", D("10"), "C-1", TODAY) == "limit_reached"


def test_per_customer_limit_only_counts_that_customer():
    add_coupon(Coupon("SAVE20", "percent", D("20"), per_customer_limit=1))
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    assert check_coupon("SAVE20", D("10"), "C-1", TODAY) == "customer_limit_reached"
    assert check_coupon("SAVE20", D("10"), "C-2", TODAY) is None


def test_reasons_are_checked_in_the_documented_order():
    add_coupon(Coupon("ALL", "percent", D("10"), starts_on=date(2026, 4, 1), min_subtotal=D("99"),
                      global_limit=0, per_customer_limit=0))
    assert check_coupon("ALL", D("1"), "C-1", TODAY) == "not_started"
    add_coupon(Coupon("LATE", "percent", D("10"), expires_on=date(2026, 1, 1), min_subtotal=D("99")))
    assert check_coupon("LATE", D("1"), "C-1", TODAY) == "expired"
    add_coupon(Coupon("LIM", "percent", D("10"), min_subtotal=D("99"), global_limit=0))
    assert check_coupon("LIM", D("1"), "C-1", TODAY) == "below_minimum"
    add_coupon(Coupon("BOTH", "percent", D("10"), global_limit=0, per_customer_limit=0))
    assert check_coupon("BOTH", D("1"), "C-1", TODAY) == "limit_reached"

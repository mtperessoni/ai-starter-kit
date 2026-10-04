"""Hidden tests for L5: percent coupon is applied before the bundle.

Rule IDs: PRM-05, PRM-09, PRM-02. Only the public API is used.
"""
from decimal import Decimal as D

from market import api


def _quote(items, coupons=()):
    api.reset()
    api.seed_demo()
    cart = api.create_cart("C-REG")
    for sku, qty in items:
        api.add_to_cart(cart, sku, qty)
    for code in coupons:
        api.apply_coupon(cart, code)
    return api.quote_cart(cart)


def test_bundle_with_percent_coupon_discount_is_25():
    """PRM-05: coupon 10.00 on 100.00 first, then bundle 15.00, so 25.00 off."""
    q = _quote([("BK-100", 1), ("BK-200", 1)], ["SAVE10"])
    assert q.discount_total == D("25.00")


def test_bundle_with_percent_coupon_total_is_75():
    """PRM-05: the total after both discounts is 75.00."""
    q = _quote([("BK-100", 1), ("BK-200", 1)], ["SAVE10"])
    assert q.total == D("75.00")


def test_both_discounts_are_listed():
    """PRC-06: the quote lists the bundle and the coupon."""
    q = _quote([("BK-100", 1), ("BK-200", 1)], ["SAVE10"])
    assert {d.code for d in q.discounts} == {"BUNDLE-READER", "SAVE10"}
    assert q.rejected_coupons == ()


def test_two_sets_with_percent_coupon():
    """PRM-05, PRM-09: 200.00 gets 20.00 coupon first, then 2 sets of 15.00, total 150.00."""
    q = _quote([("BK-100", 2), ("BK-200", 2)], ["SAVE10"])
    assert q.discount_total == D("50.00")
    assert q.total == D("150.00")


def test_bundle_with_20_percent_coupon():
    """PRM-05: SAVE20 on 100.00 gives 20.00 then the bundle 15.00, total 65.00."""
    q = _quote([("BK-100", 1), ("BK-200", 1)], ["SAVE20"])
    assert q.discount_total == D("35.00")
    assert q.total == D("65.00")


def test_control_bundle_alone_is_15():
    """PRM-09: the bundle alone gives 15.00 off."""
    q = _quote([("BK-100", 1), ("BK-200", 1)])
    assert q.discount_total == D("15.00")


def test_control_percent_coupon_alone():
    """PRM-02: SAVE10 on 200.00 of electronics and home gives 20.00 off."""
    q = _quote([("EL-200", 1), ("HM-100", 1)], ["SAVE10"])
    assert q.discount_total == D("20.00")


def test_control_bundle_with_fixed_coupon():
    """PRM-05, PRM-10: bundle 15.00 then FIX15 15.00, total 70.00."""
    q = _quote([("BK-100", 1), ("BK-200", 1)], ["FIX15"])
    assert q.discount_total == D("30.00")
    assert q.total == D("70.00")

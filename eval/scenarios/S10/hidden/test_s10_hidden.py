"""Hidden tests for S10: a coupon above 50% is refused.

Rule ID is illustrative: CHK-05 (coupon percent, now at most 50). Only the public API is used.
"""
from decimal import Decimal as D

import pytest

from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price="100.00"):
    return Cart([CartItem("sku-1", D(price), 1)])


def test_a_coupon_of_exactly_fifty_percent_is_accepted():
    """CHK-05: 50% is capped by the 30% rule: 30.00 off 100.00, shipping 15.00, total 85.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("HALF", D("50")))
    assert r.discount == D("30.00")
    assert r.total == D("85.00")


def test_a_coupon_just_above_fifty_percent_is_refused():
    """CHK-05"""
    with pytest.raises(ValueError):
        checkout(_cart(), Customer("c1"), Coupon("TOO", D("50.01")))


def test_a_coupon_of_a_hundred_percent_is_refused():
    """CHK-05"""
    with pytest.raises(ValueError):
        checkout(_cart(), Customer("c1"), Coupon("ALL", D("100")))


def test_a_zero_percent_coupon_is_still_refused():
    """CHK-05"""
    with pytest.raises(ValueError):
        checkout(_cart(), Customer("c1"), Coupon("NONE", D("0")))


def test_a_normal_coupon_is_unchanged():
    """PRC-02: 10% off 100.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("TEN", D("10")))
    assert r.discount == D("10.00")


def test_vip_and_coupon_still_add_up():
    """PRC-04: VIP 15% plus 10% is 25.00 off."""
    r = checkout(_cart(), Customer("c1", vip=True), Coupon("TEN", D("10")))
    assert r.discount == D("25.00")

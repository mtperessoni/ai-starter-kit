"""Hidden tests for S1: non-VIP discount cap of 20%, VIP keeps 30%.

Rule IDs are illustrative: PRC-03 (cap) and PRC-04 (non-VIP cap). Only the public API is used.
"""
from decimal import Decimal as D

from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price="100.00", qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_nonvip_coupon_above_cap_is_limited_to_20_percent():
    """PRC-04: non-VIP with a 25% coupon on 100.00 gets 20.00 off."""
    r = checkout(_cart(), Customer("c1"), Coupon("BIG", D("25")))
    assert r.discount == D("20.00")


def test_nonvip_capped_total():
    """PRC-04, CHK-01: 100.00 - 20.00 + 15.00 shipping = 95.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("BIG", D("25")))
    assert r.total == D("95.00")


def test_nonvip_coupon_30_percent_is_limited_to_20_percent():
    """PRC-04: a 30% coupon is no longer fully honored for a non-VIP."""
    r = checkout(_cart(), Customer("c1"), Coupon("HALF", D("30")))
    assert r.discount == D("20.00")


def test_nonvip_below_cap_unchanged():
    """PRC-02, PRC-04: a 10% coupon is under the cap, discount 10.00, total 105.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("TEN", D("10")))
    assert r.discount == D("10.00")
    assert r.total == D("105.00")


def test_nonvip_exactly_at_cap():
    """PRC-04: a 20% coupon is exactly the cap, discount 20.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("TWENTY", D("20")))
    assert r.discount == D("20.00")
    assert r.total == D("95.00")


def test_vip_keeps_30_percent_cap():
    """PRC-03: VIP 15% plus 20% coupon is 35%, capped at 30% (30.00), total 85.00."""
    r = checkout(_cart(), Customer("c1", vip=True), Coupon("TWENTY", D("20")))
    assert r.discount == D("30.00")
    assert r.total == D("85.00")


def test_vip_without_coupon_unchanged():
    """PRC-01: VIP alone gets 15.00 off 100.00, total 100.00."""
    r = checkout(_cart(), Customer("c1", vip=True))
    assert r.discount == D("15.00")
    assert r.total == D("100.00")

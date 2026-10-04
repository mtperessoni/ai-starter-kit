"""Hidden tests for S3: free shipping at exactly 200.00 after discounts.

Rule ID is illustrative: SHP-02. Only the public API is used.
"""
from decimal import Decimal as D

from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price, qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_exactly_200_is_free():
    """SHP-02: subtotal 200.00 and no discount ships for free, total 200.00."""
    r = checkout(_cart("200.00"), Customer("c1"))
    assert r.shipping == D("0.00")
    assert r.total == D("200.00")


def test_199_99_pays_shipping():
    """SHP-02, SHP-01: 199.99 pays 15.00 shipping, total 214.99."""
    r = checkout(_cart("199.99"), Customer("c1"))
    assert r.shipping == D("15.00")
    assert r.total == D("214.99")


def test_200_01_is_free():
    """SHP-02: 200.01 ships for free, total 200.01."""
    r = checkout(_cart("200.01"), Customer("c1"))
    assert r.shipping == D("0.00")
    assert r.total == D("200.01")


def test_exactly_200_after_coupon_is_free():
    """SHP-02: 250.00 with a 20% coupon is 200.00 after discounts, free shipping."""
    r = checkout(_cart("250.00"), Customer("c1"), Coupon("TWENTY", D("20")))
    assert r.discount == D("50.00")
    assert r.shipping == D("0.00")
    assert r.total == D("200.00")


def test_below_200_after_discount_pays_shipping():
    """SHP-02: VIP on 200.00 gets 30.00 off, 170.00 is below the threshold, pays 15.00."""
    r = checkout(_cart("200.00"), Customer("c1", vip=True))
    assert r.shipping == D("15.00")
    assert r.total == D("185.00")


def test_two_items_summing_to_200_are_free():
    """SHP-02: 2 x 100.00 is 200.00, free shipping."""
    r = checkout(_cart("100.00", qty=2), Customer("c1"))
    assert r.shipping == D("0.00")
    assert r.total == D("200.00")

"""Hidden tests for S4: behavior of every rule is unchanged after splitting checkout.

Rule IDs are illustrative (PRC-*, SHP-*, CHK-*). They avoid exactly 200.00 after discounts
so they also pass on a seed that still has the SHP-02 boundary bug. Only the public API is used.
"""
from decimal import Decimal as D

from orders import Cart, CartItem, Coupon, Customer, Receipt, checkout


def _cart(price="100.00", qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_vip_gets_15_percent():
    """PRC-01: VIP on 100.00 gets 15.00 off, total 100.00."""
    r = checkout(_cart(), Customer("c1", vip=True))
    assert r.discount == D("15.00")
    assert r.total == D("100.00")


def test_coupon_gives_its_percentage():
    """PRC-02: a 10% coupon gives 10.00 off 100.00, total 105.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("TEN", D("10")))
    assert r.discount == D("10.00")
    assert r.total == D("105.00")


def test_discount_capped_at_30_percent():
    """PRC-03: VIP 15% plus a 20% coupon is capped at 30.00, total 85.00."""
    r = checkout(_cart(), Customer("c1", vip=True), Coupon("TWENTY", D("20")))
    assert r.discount == D("30.00")
    assert r.total == D("85.00")


def test_shipping_costs_15():
    """SHP-01: a 100.00 order pays 15.00 shipping."""
    r = checkout(_cart(), Customer("c1"))
    assert r.shipping == D("15.00")


def test_shipping_free_above_threshold():
    """SHP-02: 200.01 after discounts ships for free, total 200.01."""
    r = checkout(_cart("200.01"), Customer("c1"))
    assert r.shipping == D("0.00")
    assert r.total == D("200.01")


def test_shipping_charged_below_threshold():
    """SHP-02, SHP-01: 199.99 pays 15.00, total 214.99."""
    r = checkout(_cart("199.99"), Customer("c1"))
    assert r.shipping == D("15.00")
    assert r.total == D("214.99")


def test_total_rounds_half_up():
    """CHK-01: 3.345 + 15.00 = 18.345 rounds half up to 18.35, not 18.34 as banker rounding would."""
    r = checkout(_cart("3.345"), Customer("c1"))
    assert r.total == D("18.35")


def test_receipt_shape():
    """CHK-02: checkout returns a Receipt with Decimal subtotal, discount, shipping, total."""
    r = checkout(_cart(), Customer("c1"), Coupon("TEN", D("10")))
    assert isinstance(r, Receipt)
    assert r.subtotal == D("100.00")
    for field in (r.subtotal, r.discount, r.shipping, r.total):
        assert isinstance(field, D)
    assert r.total == r.subtotal - r.discount + r.shipping

"""Hidden tests for S5: free shipping for every VIP order, regular customers unchanged.

Rule IDs are illustrative: SHP-01 (flat fee, now with a VIP exception) and SHP-02 (free threshold).
Only the public API is used.
"""
from decimal import Decimal as D

from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price="100.00", qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_vip_without_coupon_ships_free_below_the_threshold():
    """SHP-01: a VIP order of 100.00 gets 15.00 off and 0.00 shipping, total 85.00."""
    r = checkout(_cart(), Customer("c1", vip=True))
    assert r.shipping == D("0.00")
    assert r.total == D("85.00")


def test_vip_with_coupon_ships_free():
    """SHP-01: VIP 15% plus a 10% coupon on 100.00 is 25.00 off, 0.00 shipping, total 75.00."""
    r = checkout(_cart(), Customer("c1", vip=True), Coupon("TEN", D("10")))
    assert r.discount == D("25.00")
    assert r.shipping == D("0.00")
    assert r.total == D("75.00")


def test_vip_small_cart_ships_free():
    """SHP-01: a VIP order of 20.00 gets 3.00 off and 0.00 shipping, total 17.00."""
    r = checkout(_cart("20.00"), Customer("c1", vip=True))
    assert r.shipping == D("0.00")
    assert r.total == D("17.00")


def test_regular_customer_below_threshold_still_pays_shipping():
    """SHP-01: a regular order of 100.00 pays 15.00 shipping, total 115.00."""
    r = checkout(_cart(), Customer("c1"))
    assert r.shipping == D("15.00")
    assert r.total == D("115.00")


def test_regular_customer_with_coupon_still_pays_shipping():
    """SHP-01: a regular order of 100.00 with a 10% coupon pays 15.00 shipping, total 105.00."""
    r = checkout(_cart(), Customer("c1"), Coupon("TEN", D("10")))
    assert r.shipping == D("15.00")
    assert r.total == D("105.00")


def test_regular_customer_above_the_threshold_ships_free():
    """SHP-02: a regular order of 250.00 ships free, total 250.00."""
    r = checkout(_cart("250.00"), Customer("c1"))
    assert r.shipping == D("0.00")
    assert r.total == D("250.00")


def test_receipt_text_keeps_the_shipping_line_for_a_vip():
    """CHK-07: the receipt of a VIP order still lists Shipping, with 0.00."""
    text = checkout(_cart(), Customer("c1", vip=True)).render()
    lines = [line.split(":")[0] for line in text.splitlines()]
    assert lines == ["Subtotal", "Discount", "Shipping", "Total"]
    assert text.splitlines()[2].rstrip().endswith("0.00")

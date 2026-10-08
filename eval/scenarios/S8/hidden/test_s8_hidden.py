"""Hidden tests for S8: express delivery and loyalty points on the receipt.

Rule IDs are illustrative: SHP-03 (express delivery), LOY-01 (loyalty points). The fee of a normal
delivery is 15.00 up to 200.00 after discounts and free above it. Only the public API is used.
"""
from decimal import Decimal as D

from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price, qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_express_costs_a_flat_fee():
    """SHP-03: 100.00 with express: shipping 25.00, total 125.00."""
    r = checkout(_cart("100.00"), Customer("c1"), express=True)
    assert r.shipping == D("25.00")
    assert r.total == D("125.00")


def test_express_is_never_free_above_the_free_shipping_amount():
    """SHP-03: 300.00 ships free normally, but express still costs 25.00."""
    assert checkout(_cart("300.00"), Customer("c1")).shipping == D("0.00")
    r = checkout(_cart("300.00"), Customer("c1"), express=True)
    assert r.shipping == D("25.00")
    assert r.total == D("325.00")


def test_express_is_the_same_for_a_vip():
    """SHP-03: a VIP pays the same flat 25.00."""
    r = checkout(_cart("100.00"), Customer("c1", vip=True), express=True)
    assert r.shipping == D("25.00")


def test_express_off_by_default_keeps_normal_shipping():
    """SHP-03: no express means today's rule: 15.00 at 100.00."""
    assert checkout(_cart("100.00"), Customer("c1")).shipping == D("15.00")
    assert checkout(_cart("100.00"), Customer("c1"), express=False).shipping == D("15.00")


def test_points_one_per_full_ten_after_discounts():
    """LOY-01: 100.00 earns 10 points, 99.99 earns 9."""
    assert checkout(_cart("100.00"), Customer("c1")).points == 10
    assert checkout(_cart("99.99"), Customer("c1")).points == 9


def test_points_do_not_count_shipping():
    """LOY-01: 30.00 (shipping 15.00) earns 3 points, express (25.00) the same 3."""
    assert checkout(_cart("30.00"), Customer("c1")).points == 3
    assert checkout(_cart("30.00"), Customer("c1"), express=True).points == 3


def test_vip_earns_double_points():
    """LOY-01: a VIP at 100.00 before the VIP discount earns points on the amount after discounts, doubled."""
    plain = checkout(_cart("100.00"), Customer("c1"))
    vip = checkout(_cart("100.00"), Customer("c1", vip=True))
    assert plain.points == 10
    assert vip.points == 2 * ((vip.subtotal - vip.discount) // D("10"))


def test_points_use_the_amount_after_a_coupon():
    """LOY-01: a 10% coupon on 100.00 leaves 90.00: 9 points."""
    r = checkout(_cart("100.00"), Customer("c1"), Coupon("TEN", D("10")))
    assert r.points == 9


def test_receipt_layout_and_dict_are_unchanged():
    """LOY-01: points are a field, not a receipt line and not an as_dict key."""
    r = checkout(_cart("100.00"), Customer("c1"))
    assert set(r.as_dict()) == {"subtotal", "discount", "shipping", "total"}
    assert "oints" not in r.render()

"""Hidden tests for L1: free shipping is judged after loyalty redemption.

Rule IDs: SHP-03, CHK-04, LOY-04, CHK-03. Only the public API is used.
"""
from decimal import Decimal as D

from market import api

ADDR = api.Address("BR", "SP", "01000-000")
OK = api.PaymentRequest("card", "ok_1")


def _cart(customer, items):
    api.reset()
    api.seed_demo()
    cart = api.create_cart(customer)
    for sku, qty in items:
        api.add_to_cart(cart, sku, qty)
    return cart


def _lamp_headphones(customer="C-REG"):
    return _cart(customer, [("EL-200", 1), ("HM-100", 1)])


def test_points_remove_free_shipping_fee():
    """SHP-03, CHK-04: 200.00 minus 5.00 of points is below 200.00, so shipping is 16.00."""
    cart = _lamp_headphones()
    api.grant_points("C-REG", 500)
    q = api.quote_order(cart, ADDR, points_to_redeem=500)
    assert q.shipping.fee == D("16.00")


def test_points_quote_tax_includes_shipping_tax():
    """CHK-04, TAX-03, TAX-04: tax is 16.00 on lines plus 1.28 on shipping, not reduced by points."""
    cart = _lamp_headphones()
    api.grant_points("C-REG", 500)
    q = api.quote_order(cart, ADDR, points_to_redeem=500)
    assert q.tax.total == D("17.28")


def test_points_quote_loyalty_discount():
    """LOY-04: 500 points are worth 5.00."""
    cart = _lamp_headphones()
    api.grant_points("C-REG", 500)
    q = api.quote_order(cart, ADDR, points_to_redeem=500)
    assert q.loyalty_discount == D("5.00")


def test_points_quote_total():
    """CHK-03: 200.00 + 16.00 + 17.28 - 5.00 = 228.28."""
    cart = _lamp_headphones()
    api.grant_points("C-REG", 500)
    q = api.quote_order(cart, ADDR, points_to_redeem=500)
    assert q.total == D("228.28")


def test_control_without_points_is_free_and_total_216():
    """SHP-03: without points merchandise is 200.00, shipping is free, total 200.00 + 16.00 tax."""
    cart = _lamp_headphones()
    q = api.quote_order(cart, ADDR)
    assert q.shipping.fee == D("0.00")
    assert q.total == D("216.00")


def test_placed_order_with_points_pays_shipping():
    """CHK-02, CHK-04, SHP-03: the placed order keeps the quote amounts."""
    cart = _lamp_headphones()
    api.grant_points("C-REG", 500)
    order = api.place_order(cart, OK, ADDR, points_to_redeem=500)
    assert order.status == "paid"
    assert order.shipping == D("16.00")
    assert order.loyalty_discount == D("5.00")
    assert order.total == D("228.28")


def test_vip_keeps_free_shipping_after_redemption():
    """SHP-03, LOY-04: VIP with 120.00 of merchandise and 5.00 of points is still above 100.00."""
    cart = _cart("C-VIP", [("EL-200", 1)])
    api.grant_points("C-VIP", 500)
    q = api.quote_order(cart, ADDR, points_to_redeem=500)
    assert q.shipping.fee == D("0.00")
    assert q.loyalty_discount == D("5.00")
    assert q.total == D("124.60")


def test_large_cart_keeps_free_shipping_after_redemption():
    """SHP-03: 240.00 minus 5.00 is still above 200.00, shipping stays free."""
    cart = _cart("C-REG", [("EL-200", 2)])
    api.grant_points("C-REG", 500)
    q = api.quote_order(cart, ADDR, points_to_redeem=500)
    assert q.shipping.fee == D("0.00")

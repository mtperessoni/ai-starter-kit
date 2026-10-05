"""Hidden tests for L4: a declined payment gives the single-use coupon back.

Rule IDs: CHK-06, PRM-04, CHK-10. Only the public API is used.
"""
from decimal import Decimal as D

import pytest

from market import api

ADDR = api.Address("BR", "SP", "01000-000")
OK = api.PaymentRequest("card", "ok_1")
DECLINE = api.PaymentRequest("card", "decline_1")


def _cart(customer="C-REG", sku="EL-200", coupon="SAVE20"):
    api.reset()
    api.seed_demo()
    cart = api.create_cart(customer)
    api.add_to_cart(cart, sku, 1)
    if coupon:
        api.apply_coupon(cart, coupon)
    return cart


def test_retry_with_same_coupon_after_decline_is_paid():
    """CHK-06, PRM-04, CHK-10: the second attempt with the same coupon is paid with SAVE20 applied."""
    cart = _cart()
    first = api.place_order(cart, DECLINE, ADDR)
    assert first.status == "payment_failed"
    second = api.place_order(cart, OK, ADDR)
    assert second.status == "paid"
    assert second.discount_total == D("24.00")
    assert second.total == D("114.48")


def test_two_declines_then_success_is_paid():
    """CHK-06, PRM-04: every declined attempt gives the use back."""
    cart = _cart()
    assert api.place_order(cart, DECLINE, ADDR).status == "payment_failed"
    assert api.place_order(cart, DECLINE, ADDR).status == "payment_failed"
    assert api.place_order(cart, OK, ADDR).status == "paid"


def test_decline_state_releases_stock_and_records_code():
    """CHK-06: after a decline the order is payment_failed and the stock is available again."""
    cart = _cart()
    order = api.place_order(cart, DECLINE, ADDR)
    assert order.status == "payment_failed"
    assert order.decline_code == "card_declined"
    assert api.available_stock("EL-200") == 5


def test_decline_without_coupon_can_be_retried():
    """CHK-06: control, a decline without any coupon is retried successfully."""
    cart = _cart(coupon=None)
    assert api.place_order(cart, DECLINE, ADDR).status == "payment_failed"
    assert api.place_order(cart, OK, ADDR).status == "paid"


def test_cancel_gives_the_single_use_back():
    """CHK-09, PRM-04: after a paid order is cancelled the coupon can be used on a new cart."""
    cart = _cart()
    order = api.place_order(cart, OK, ADDR)
    assert order.status == "paid"
    api.cancel_order(order.order_id)
    cart2 = api.create_cart("C-REG")
    api.add_to_cart(cart2, "EL-200", 1)
    api.apply_coupon(cart2, "SAVE20")
    assert api.place_order(cart2, OK, ADDR).status == "paid"


def test_paid_order_uses_the_coupon_up():
    """PRM-04: a captured payment counts the use for good, so a new cart cannot use it again."""
    cart = _cart()
    assert api.place_order(cart, OK, ADDR).status == "paid"
    cart2 = api.create_cart("C-REG")
    api.add_to_cart(cart2, "EL-200", 1)
    with pytest.raises(api.MarketError):
        api.apply_coupon(cart2, "SAVE20")

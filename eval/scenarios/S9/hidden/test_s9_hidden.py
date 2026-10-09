"""Hidden tests for S9: the premise is wrong, so checkout must stay exactly as it is.

Checkout is stateless and VIP is a flag the storefront sends. Only the public API is used.
"""
import inspect
from decimal import Decimal as D

import orders
from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price, qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_a_big_cart_does_not_make_a_regular_customer_vip():
    """PRC-01: 600.00 for a customer without the flag gets no VIP discount."""
    r = checkout(_cart("600.00"), Customer("c1"))
    assert r.discount == D("0.00")
    assert r.total == D("600.00")


def test_the_flag_still_gives_the_vip_discount():
    """PRC-01: a flagged customer gets 15% off 100.00, shipping 15.00, total 100.00."""
    r = checkout(_cart("100.00"), Customer("c1", vip=True))
    assert r.discount == D("15.00")
    assert r.total == D("100.00")


def test_the_same_call_gives_the_same_receipt_twice():
    """Constitution II: no history, no clock: two identical calls, two identical receipts."""
    first = checkout(_cart("300.00"), Customer("c1"))
    assert checkout(_cart("300.00"), Customer("c1")) == first


def test_checkout_signature_is_unchanged():
    """Constitution V: no history or month argument was added."""
    names = list(inspect.signature(checkout).parameters)
    assert names[:3] == ["cart", "customer", "coupon"]
    assert not any(n in names for n in ("history", "orders", "month", "spent", "month_total"))


def test_the_customer_type_has_no_spend_field():
    """Constitution V: Customer keeps id and vip."""
    fields = set(inspect.signature(Customer).parameters)
    assert {"id", "vip"} <= fields
    assert not any("spend" in f or "month" in f or "history" in f for f in fields)


def test_public_names_are_unchanged():
    assert sorted(orders.__all__) == ["Cart", "CartItem", "Coupon", "Customer", "Receipt", "checkout"]


def test_coupon_still_adds_to_the_vip_percentage():
    """PRC-04: VIP 15% plus a 10% coupon on 100.00 is 25.00 off."""
    r = checkout(_cart("100.00"), Customer("c1", vip=True), Coupon("TEN", D("10")))
    assert r.discount == D("25.00")

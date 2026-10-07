"""Hidden tests for S7: a minimum order of 30.00 for everybody.

Rule ID is illustrative: CHK-08. The carts use no discount, so the subtotal and the amount after
discounts are equal and the open question (before or after discounts) does not change any result.
Only the public API is used.
"""
from decimal import Decimal as D

import pytest

from orders import Cart, CartItem, Customer, checkout


def _cart(price, qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_cart_below_the_minimum_is_refused():
    """CHK-08: 29.99 is below 30.00."""
    with pytest.raises(ValueError):
        checkout(_cart("29.99"), Customer("c1"))


def test_cart_of_exactly_the_minimum_is_accepted():
    """CHK-08: 30.00 is accepted, shipping 15.00, total 45.00."""
    r = checkout(_cart("30.00"), Customer("c1"))
    assert r.subtotal == D("30.00")
    assert r.total == D("45.00")


def test_cart_above_the_minimum_is_accepted():
    """CHK-08: 100.00 is accepted, total 115.00."""
    assert checkout(_cart("100.00"), Customer("c1")).total == D("115.00")


def test_two_lines_summing_below_the_minimum_are_refused():
    """CHK-08: the minimum applies to the cart, not per line: 10.00 plus 19.99."""
    cart = Cart([CartItem("sku-1", D("10.00"), 1), CartItem("sku-2", D("19.99"), 1)])
    with pytest.raises(ValueError):
        checkout(cart, Customer("c1"))


def test_two_lines_summing_to_the_minimum_are_accepted():
    """CHK-08: 10.00 plus 20.00."""
    cart = Cart([CartItem("sku-1", D("10.00"), 1), CartItem("sku-2", D("20.00"), 1)])
    assert checkout(cart, Customer("c1")).subtotal == D("30.00")


def test_the_minimum_does_not_depend_on_who_buys():
    """CHK-08: the same cart of 29.99 is refused for two different customers."""
    for customer_id in ("c1", "c2"):
        with pytest.raises(ValueError):
            checkout(_cart("29.99"), Customer(customer_id))


def test_empty_cart_is_still_refused():
    """CHK-03: unchanged."""
    with pytest.raises(ValueError):
        checkout(Cart([]), Customer("c1"))

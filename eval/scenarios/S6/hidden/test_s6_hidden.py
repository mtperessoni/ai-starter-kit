"""Hidden tests for S6: a line priced at 0.00 is refused; every other validation is unchanged.

Rule ID is illustrative: CHK-04 (item validation). Only the public API is used.
"""
from decimal import Decimal as D

import pytest

from orders import Cart, CartItem, Customer, checkout


def _cart(*lines):
    return Cart([CartItem(sku, D(price), qty) for sku, price, qty in lines])


def test_zero_priced_line_is_refused():
    """CHK-04: a single line of 0.00 refuses the order."""
    with pytest.raises(ValueError):
        checkout(_cart(("sku-1", "0.00", 1)), Customer("c1"))


def test_zero_priced_line_among_valid_lines_refuses_the_whole_order():
    """CHK-04: no partial receipt when one line is unpriced."""
    with pytest.raises(ValueError):
        checkout(_cart(("sku-1", "40.00", 2), ("sku-2", "0.00", 1)), Customer("c1"))


def test_zero_priced_line_is_refused_with_many_units():
    """CHK-04: the quantity does not make an unpriced line sellable."""
    with pytest.raises(ValueError):
        checkout(_cart(("sku-1", "0.00", 5)), Customer("c1"))


def test_one_cent_line_is_accepted():
    """CHK-04: 0.01 is above zero, so the order goes through: subtotal 0.01, shipping 15.00."""
    r = checkout(_cart(("sku-1", "0.01", 1)), Customer("c1"))
    assert r.subtotal == D("0.01")
    assert r.total == D("15.01")


def test_negative_price_is_still_refused():
    """CHK-04: unchanged."""
    with pytest.raises(ValueError):
        checkout(_cart(("sku-1", "-1.00", 1)), Customer("c1"))


def test_quantity_below_one_is_still_refused():
    """CHK-04: unchanged."""
    with pytest.raises(ValueError):
        checkout(_cart(("sku-1", "10.00", 0)), Customer("c1"))


def test_empty_cart_is_still_refused():
    """CHK-03: unchanged."""
    with pytest.raises(ValueError):
        checkout(Cart([]), Customer("c1"))


def test_regular_order_is_unchanged():
    """CHK-01: two lines of 40.00 total 95.00 with 15.00 shipping."""
    r = checkout(_cart(("sku-1", "40.00", 2)), Customer("c1"))
    assert r.total == D("95.00")

"""Tests for order_validation (CHK-05, CHK-07, CHK-10)."""
from decimal import Decimal

import pytest

from market.features.cart.cart_pricing import price_cart
from market.features.cart.cart_service import get_cart, set_quantity
from market.features.checkout.order_validation import describe_blockers, validate_checkout
from market.features.checkout.tests.helpers import ADDR, cart_with
from market.infra import config
from market.infra.errors import ValidationError
from market.infra.models import Address


def check(cart_id, address=ADDR):
    validate_checkout(get_cart(cart_id), address, price_cart(cart_id))


def test_a_valid_physical_order_passes():
    check(cart_with("C-REG", [("EL-200", 1)]))


def test_physical_items_need_an_address():
    with pytest.raises(ValidationError, match="address"):
        check(cart_with("C-REG", [("EL-200", 1)]), None)


def test_a_blank_region_is_not_an_address():
    with pytest.raises(ValidationError, match="address"):
        check(cart_with("C-REG", [("EL-200", 1)]), Address("BR", " ", ""))


def test_gift_cards_only_need_no_address():
    check(cart_with("C-REG", [("GC-050", 1)]), None)


def test_a_gift_card_with_a_physical_item_needs_an_address():
    with pytest.raises(ValidationError, match="address"):
        check(cart_with("C-REG", [("GC-050", 1), ("BK-100", 1)]), None)


def test_a_coupon_that_stopped_being_valid_blocks_the_order():
    cart_id = cart_with("C-REG", [("BK-100", 2)], ("SAVE10",))
    set_quantity(cart_id, "BK-100", 1)
    with pytest.raises(ValidationError, match="SAVE10.*below_minimum"):
        check(cart_id)


def test_merchandise_below_the_minimum_is_refused():
    with pytest.raises(ValidationError, match="at least"):
        check(cart_with("C-REG", [("PN-001", 1)]))


def test_minimum_is_checked_after_discounts():
    cart_id = cart_with("C-REG", [("EL-200", 1)], ("SAVE20",))
    config.set("checkout.min_order_total", Decimal("100.00"))
    with pytest.raises(ValidationError):
        check(cart_id)


def test_minimum_follows_config():
    config.set("checkout.min_order_total", Decimal("5.00"))
    check(cart_with("C-REG", [("PN-001", 1)]))


def test_an_empty_cart_is_refused():
    cart_id = cart_with("C-REG", [])
    with pytest.raises(ValidationError, match="empty"):
        check(cart_id)


def test_describe_blockers_lists_every_problem():
    cart_id = cart_with("C-REG", [("PN-001", 1)], ())
    blockers = describe_blockers(get_cart(cart_id), None, price_cart(cart_id))
    assert len(blockers) == 2 and "address" in blockers[0] and "at least" in blockers[1]


def test_describe_blockers_is_empty_for_a_valid_order():
    cart_id = cart_with("C-REG", [("EL-200", 1)])
    assert describe_blockers(get_cart(cart_id), ADDR, price_cart(cart_id)) == []


def test_describe_blockers_names_rejected_coupons_and_an_empty_cart():
    cart_id = cart_with("C-REG", [("BK-100", 2)], ("SAVE10",))
    set_quantity(cart_id, "BK-100", 1)
    assert describe_blockers(get_cart(cart_id), ADDR, price_cart(cart_id)) == [
        "coupon SAVE10 is not valid: below_minimum"]
    empty = cart_with("C-REG", [])
    assert describe_blockers(get_cart(empty), ADDR, price_cart(empty)) == ["the cart is empty"]

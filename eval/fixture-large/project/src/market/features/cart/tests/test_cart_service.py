"""Tests for cart_service (CRT-01 to CRT-05, CRT-07, CAT-05)."""
from decimal import Decimal

import pytest

from market.features.cart.cart_service import (add_item, clear_cart, create_cart, get_cart,
                                               mark_converted, remove_item, set_quantity)
from market.features.catalog.product_store import add_product, deactivate_product
from market.features.inventory.stock_store import set_on_hand
from market.infra import clock, config
from market.infra.customers import add_customer
from market.infra.errors import NotFoundError, OutOfStockError, PolicyError, ValidationError
from market.infra.models import Customer, Product


@pytest.fixture(autouse=True)
def world():
    add_customer(Customer("C-1", "one@example.com"))
    for sku, category, price in [("BK-100", "books", "40.00"), ("EL-200", "electronics", "120.00"),
                                 ("HM-100", "home", "80.00"), ("GC-050", "gift_card", "50.00")]:
        add_product(Product(sku, sku, category, Decimal(price), 0 if sku == "GC-050" else 100))
        set_on_hand(sku, 5 if sku == "EL-200" else 200)


@pytest.fixture
def cart_id():
    return create_cart("C-1").cart_id


def lines(cart_id):
    return [(l.sku, l.qty) for l in get_cart(cart_id).lines]


def test_create_cart_is_open_and_empty():
    cart = create_cart("C-1")
    assert cart.cart_id == "CRT-0001" and cart.status == "open" and cart.lines == []


def test_create_cart_for_unknown_customer_fails():
    with pytest.raises(NotFoundError):
        create_cart("C-X")


def test_add_item_adds_a_line(cart_id):
    add_item(cart_id, "BK-100", 2)
    assert lines(cart_id) == [("BK-100", 2)]


def test_adding_the_same_sku_adds_to_its_quantity(cart_id):
    add_item(cart_id, "BK-100", 2)
    add_item(cart_id, "BK-100")
    assert lines(cart_id) == [("BK-100", 3)]


def test_quantity_stays_within_ninety_nine(cart_id):
    add_item(cart_id, "BK-100", 99)
    with pytest.raises(ValidationError):
        add_item(cart_id, "BK-100", 1)
    assert lines(cart_id) == [("BK-100", 99)]


def test_quantity_limit_comes_from_config(cart_id):
    config.set("cart.max_qty", 3)
    with pytest.raises(ValidationError):
        add_item(cart_id, "BK-100", 4)


def test_quantity_below_one_is_invalid(cart_id):
    with pytest.raises(ValidationError):
        add_item(cart_id, "BK-100", 0)


def test_cart_has_at_most_twenty_different_skus(cart_id):
    config.set("cart.max_lines", 2)
    add_item(cart_id, "BK-100")
    add_item(cart_id, "HM-100")
    with pytest.raises(ValidationError):
        add_item(cart_id, "EL-200")
    add_item(cart_id, "BK-100")
    assert lines(cart_id) == [("BK-100", 2), ("HM-100", 1)]


def test_unknown_product_cannot_be_added(cart_id):
    with pytest.raises(NotFoundError):
        add_item(cart_id, "NOPE-1")


def test_inactive_product_cannot_be_added(cart_id):
    deactivate_product("BK-100")
    with pytest.raises(ValidationError):
        add_item(cart_id, "BK-100")


def test_quantity_above_available_stock_cannot_be_added(cart_id):
    with pytest.raises(OutOfStockError) as caught:
        add_item(cart_id, "EL-200", 6)
    assert caught.value.skus == ("EL-200",)
    add_item(cart_id, "EL-200", 5)
    with pytest.raises(OutOfStockError):
        add_item(cart_id, "EL-200")


def test_gift_cards_ignore_stock(cart_id):
    add_item(cart_id, "GC-050", 50)
    assert lines(cart_id) == [("GC-050", 50)]


def test_set_quantity_replaces_the_quantity(cart_id):
    add_item(cart_id, "BK-100", 2)
    set_quantity(cart_id, "BK-100", 7)
    assert lines(cart_id) == [("BK-100", 7)]


def test_set_quantity_zero_removes_the_line(cart_id):
    add_item(cart_id, "BK-100", 2)
    set_quantity(cart_id, "BK-100", 0)
    assert lines(cart_id) == []


def test_set_quantity_checks_range_and_stock(cart_id):
    add_item(cart_id, "EL-200", 1)
    with pytest.raises(ValidationError):
        set_quantity(cart_id, "EL-200", 100)
    with pytest.raises(ValidationError):
        set_quantity(cart_id, "EL-200", -1)
    with pytest.raises(OutOfStockError):
        set_quantity(cart_id, "EL-200", 6)


def test_remove_item_and_clear_cart(cart_id):
    add_item(cart_id, "BK-100")
    add_item(cart_id, "HM-100")
    remove_item(cart_id, "BK-100")
    assert lines(cart_id) == [("HM-100", 1)]
    get_cart(cart_id).coupon_codes.append("SAVE10")
    clear_cart(cart_id)
    assert lines(cart_id) == [] and get_cart(cart_id).coupon_codes == []


def test_removing_a_sku_not_in_the_cart_fails(cart_id):
    with pytest.raises(NotFoundError):
        remove_item(cart_id, "BK-100")


def test_unknown_cart_raises_not_found():
    with pytest.raises(NotFoundError):
        add_item("CRT-9999", "BK-100")


def test_an_untouched_cart_expires_and_cannot_be_changed(cart_id):
    add_item(cart_id, "BK-100")
    clock.advance(days=7)
    with pytest.raises(PolicyError):
        add_item(cart_id, "BK-100")
    with pytest.raises(PolicyError):
        remove_item(cart_id, "BK-100")


def test_touching_a_cart_resets_the_expiry_clock(cart_id):
    clock.advance(days=6)
    add_item(cart_id, "BK-100")
    clock.advance(days=6)
    add_item(cart_id, "BK-100")
    assert lines(cart_id) == [("BK-100", 2)]


def test_a_converted_cart_cannot_be_changed(cart_id):
    mark_converted(cart_id)
    assert get_cart(cart_id).status == "converted"
    with pytest.raises(PolicyError):
        add_item(cart_id, "BK-100")

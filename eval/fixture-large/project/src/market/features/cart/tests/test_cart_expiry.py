"""Tests for cart_expiry (CRT-07)."""
from decimal import Decimal

import pytest

from market.features.cart.cart_expiry import is_expired, purge_expired
from market.features.cart.cart_service import add_item, create_cart, get_cart, mark_converted
from market.features.catalog.product_store import add_product
from market.features.inventory.stock_store import set_on_hand
from market.infra import clock, config
from market.infra.customers import add_customer
from market.infra.errors import NotFoundError
from market.infra.models import Customer, Product


@pytest.fixture(autouse=True)
def world():
    add_customer(Customer("C-1", "one@example.com"))
    add_product(Product("BK-100", "Python Basics", "books", Decimal("40.00"), 400))
    set_on_hand("BK-100", 50)


def test_fresh_cart_is_not_expired():
    assert not is_expired(create_cart("C-1"))


def test_cart_expires_after_seven_days_untouched():
    cart = create_cart("C-1")
    clock.advance(days=6, hours=23)
    assert not is_expired(cart)
    clock.advance(hours=1)
    assert is_expired(cart)


def test_ttl_comes_from_config():
    config.set("cart.ttl_days", 1)
    cart = create_cart("C-1")
    clock.advance(days=1)
    assert is_expired(cart)


def test_touching_resets_the_clock():
    cart = create_cart("C-1")
    clock.advance(days=5)
    add_item(cart.cart_id, "BK-100")
    clock.advance(days=5)
    assert not is_expired(get_cart(cart.cart_id))


def test_purge_removes_only_open_expired_carts():
    create_cart("C-1")
    converted = create_cart("C-1")
    mark_converted(converted.cart_id)
    clock.advance(days=8)
    fresh = create_cart("C-1")
    assert purge_expired() == 1
    assert get_cart(converted.cart_id).status == "converted"
    assert get_cart(fresh.cart_id).status == "open"


def test_purged_cart_is_gone():
    stale = create_cart("C-1")
    clock.advance(days=8)
    purge_expired()
    with pytest.raises(NotFoundError):
        get_cart(stale.cart_id)

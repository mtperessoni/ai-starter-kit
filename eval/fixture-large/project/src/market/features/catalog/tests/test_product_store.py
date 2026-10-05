"""Tests for product_store (CAT-03, CAT-04, CAT-05, CAT-06)."""
from decimal import Decimal

import pytest

from market.features.catalog.product_store import (add_product, deactivate_product, find_product,
                                                   get_product, list_products, require_sellable,
                                                   update_price)
from market.infra import config
from market.infra.errors import NotFoundError, ValidationError
from market.infra.models import Product


def make(sku="AB-100", category="toys", price="10.00", weight=100):
    return Product(sku, "Thing", category, Decimal(price), weight)


def test_add_sets_taxable_class_and_normalizes_price():
    book = add_product(make("BK-1", "books", "12.5"))
    assert book.taxable_class == "exempt" and book.price == Decimal("12.50")
    assert str(book.price) == "12.50"
    assert add_product(make("TY-1")).taxable_class == "standard"


def test_duplicate_sku_rejected():
    add_product(make())
    with pytest.raises(ValidationError):
        add_product(make())


def test_invalid_product_is_not_stored():
    with pytest.raises(ValidationError):
        add_product(make(price="0.00"))
    assert find_product("AB-100") is None


def test_get_unknown_raises_and_find_returns_none():
    with pytest.raises(NotFoundError):
        get_product("NOPE-1")
    assert find_product("NOPE-1") is None


def test_list_products_sorted_by_sku():
    add_product(make("ZZ-1"))
    add_product(make("AA-1"))
    assert [p.sku for p in list_products()] == ["AA-1", "ZZ-1"]


def test_deactivated_product_is_not_sellable_but_still_readable():
    add_product(make())
    deactivate_product("AB-100")
    assert get_product("AB-100").active is False
    with pytest.raises(ValidationError):
        require_sellable("AB-100")


def test_require_sellable_unknown_raises_not_found():
    with pytest.raises(NotFoundError):
        require_sellable("NOPE-1")


def test_update_price_applies_within_limit():
    add_product(make())
    assert update_price("AB-100", Decimal("14.00")).price == Decimal("14.00")


def test_update_price_over_limit_rejected_and_unchanged():
    add_product(make())
    with pytest.raises(ValidationError):
        update_price("AB-100", Decimal("15.01"))
    assert get_product("AB-100").price == Decimal("10.00")


def test_price_change_limit_is_configurable():
    add_product(make())
    config.set("catalog.max_price_change_percent", Decimal("100"))
    assert update_price("AB-100", Decimal("20.00")).price == Decimal("20.00")

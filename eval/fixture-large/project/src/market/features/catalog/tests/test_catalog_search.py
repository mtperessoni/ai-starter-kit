"""Tests for catalog_search (CAT-07)."""
from decimal import Decimal

import pytest

from market.features.catalog.catalog_search import search_products
from market.features.catalog.product_store import add_product, deactivate_product
from market.infra.errors import ValidationError
from market.infra.models import Product


@pytest.fixture(autouse=True)
def catalog():
    add_product(Product("BK-100", "Python Basics", "books", Decimal("40.00"), 400))
    add_product(Product("EL-100", "USB Cable", "electronics", Decimal("15.00"), 100))
    add_product(Product("EL-200", "Headphones", "electronics", Decimal("120.00"), 300))
    add_product(Product("TY-100", "Puzzle", "toys", Decimal("30.00"), 700))


def skus(found):
    return [p.sku for p in found]


def test_no_filter_returns_all_sorted_by_name():
    assert skus(search_products()) == ["EL-200", "TY-100", "BK-100", "EL-100"]


def test_query_matches_name_ignoring_case():
    assert skus(search_products("python")) == ["BK-100"]


def test_query_matches_sku():
    assert skus(search_products("el-")) == ["EL-200", "EL-100"]


def test_inactive_products_are_hidden():
    deactivate_product("BK-100")
    assert "BK-100" not in skus(search_products())


def test_category_and_max_price_filters():
    assert skus(search_products(category="electronics", max_price=Decimal("20.00"))) == ["EL-100"]


def test_sort_by_price():
    assert skus(search_products(sort="price_asc")) == ["EL-100", "TY-100", "BK-100", "EL-200"]
    assert skus(search_products(sort="price_desc")) == ["EL-200", "BK-100", "TY-100", "EL-100"]


def test_unknown_sort_rejected():
    with pytest.raises(ValidationError):
        search_products(sort="random")


def test_no_match_gives_empty_list():
    assert search_products("zzz") == []

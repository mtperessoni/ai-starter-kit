"""Tests for product_validation (CAT-01, CAT-02, CAT-03, CAT-06)."""
from decimal import Decimal

import pytest

from market.features.catalog.product_validation import (taxable_class_for, validate_price_change,
                                                        validate_product)
from market.infra import config
from market.infra.errors import ValidationError
from market.infra.models import Product


def make(**kw):
    base = dict(sku="AB-100", name="Thing", category="toys", price=Decimal("10.00"), weight_grams=100)
    base.update(kw)
    return Product(**base)


def test_valid_product_passes():
    validate_product(make())


@pytest.mark.parametrize("sku", ["AB", "ab-100", "A" * 21, "AB 100", "AB_100"])
def test_bad_sku_rejected(sku):
    with pytest.raises(ValidationError):
        validate_product(make(sku=sku))


def test_sku_boundaries_accepted():
    validate_product(make(sku="ABC"))
    validate_product(make(sku="A" * 20))


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
def test_bad_name_rejected(name):
    with pytest.raises(ValidationError):
        validate_product(make(name=name))


@pytest.mark.parametrize("price", ["0.00", "-1.00", "10.001", "100000.01"])
def test_bad_price_rejected(price):
    with pytest.raises(ValidationError):
        validate_product(make(price=Decimal(price)))


def test_max_price_comes_from_config():
    config.set("catalog.max_price", Decimal("20.00"))
    with pytest.raises(ValidationError):
        validate_product(make(price=Decimal("20.01")))
    validate_product(make(price=Decimal("20.00")))


def test_category_must_be_known():
    with pytest.raises(ValidationError):
        validate_product(make(category="garden"))


@pytest.mark.parametrize("weight", [0, 30001])
def test_weight_range(weight):
    with pytest.raises(ValidationError):
        validate_product(make(weight_grams=weight))


def test_gift_card_weighs_zero():
    validate_product(make(category="gift_card", weight_grams=0))
    with pytest.raises(ValidationError):
        validate_product(make(category="gift_card", weight_grams=5))


def test_taxable_class_by_category():
    assert taxable_class_for("books") == "exempt"
    assert taxable_class_for("gift_card") == "exempt"
    assert taxable_class_for("electronics") == "standard"


def test_price_change_within_fifty_percent():
    validate_price_change(Decimal("100.00"), Decimal("150.00"))
    validate_price_change(Decimal("100.00"), Decimal("50.00"))


def test_price_change_over_fifty_percent_rejected():
    with pytest.raises(ValidationError):
        validate_price_change(Decimal("100.00"), Decimal("150.01"))
    with pytest.raises(ValidationError):
        validate_price_change(Decimal("100.00"), Decimal("49.99"))

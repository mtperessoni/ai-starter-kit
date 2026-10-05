"""Tests for shipping_rules (SHP-02, SHP-03, SHP-04)."""
from decimal import Decimal

import pytest

from market.features.pricing.quote_models import LineQuote
from market.features.shipping.shipping_rules import (free_threshold, is_digital_only, is_overweight,
                                                     started_steps, total_weight, weight_surcharge)
from market.infra import config


def line(category="electronics", qty=1, weight=300, price="120.00", sku="EL-200"):
    unit = Decimal(price)
    return LineQuote(sku, category, qty, unit, unit * qty, Decimal("0.00"), unit * qty, "standard", weight)


def test_gift_cards_only_is_digital():
    assert is_digital_only([line("gift_card", 2, 0, "50.00", "GC-050")]) is True


def test_gift_card_with_a_book_is_not_digital():
    assert is_digital_only([line("gift_card", 1, 0, "50.00", "GC-050"), line("books", 1, 400, "40.00", "BK-100")]) is False


def test_empty_order_is_not_digital():
    assert is_digital_only([]) is False


def test_total_weight_multiplies_by_quantity():
    assert total_weight([line(qty=2, weight=400), line("home", 1, 1500, "80.00", "HM-100")]) == 2300


def test_total_weight_skips_gift_cards():
    assert total_weight([line("gift_card", 3, 50, "50.00", "GC-050"), line(weight=300)]) == 300


@pytest.mark.parametrize("grams,expected", [
    (0, "0.00"), (1000, "0.00"), (1001, "3.00"), (1500, "3.00"), (1501, "6.00"), (1800, "6.00"),
    (30000, "174.00"),
])
def test_weight_surcharge_steps(grams, expected):
    assert weight_surcharge(grams) == Decimal(expected)


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError):
        weight_surcharge(-1)


def test_surcharge_step_follows_config():
    config.set("shipping.surcharge_per_500g", Decimal("5.00"))
    assert weight_surcharge(1800) == Decimal("10.00")


def test_free_threshold_standard_and_vip():
    assert free_threshold("standard") == Decimal("200.00")
    assert free_threshold("vip") == Decimal("100.00")


def test_free_threshold_follows_config():
    config.set("shipping.free_threshold", Decimal("150.00"))
    assert free_threshold("standard") == Decimal("150.00")


@pytest.mark.parametrize("grams,steps", [(0, 0), (1000, 0), (1001, 1), (1500, 1), (1501, 2)])
def test_started_steps(grams, steps):
    assert started_steps(grams) == steps


def test_overweight_follows_the_configured_limit():
    assert is_overweight(30001) is True and is_overweight(30000) is False
    config.set("shipping.max_weight_grams", 5000)
    assert is_overweight(5001) is True

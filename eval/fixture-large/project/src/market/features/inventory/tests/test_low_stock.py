"""Tests for low_stock (INV-08)."""
from decimal import Decimal

import pytest

from market.features.catalog.product_store import add_product
from market.features.inventory.low_stock import check_low_stock
from market.features.inventory.reservations import reserve
from market.features.inventory.stock_store import set_on_hand
from market.infra import config, events
from market.infra.models import Product


def test_event_when_crossing_from_above_five_to_five_or_below():
    check_low_stock("EL-200", 6, 5)
    assert events.history("inventory.low_stock")[0].payload == {"sku": "EL-200", "available": 5}


@pytest.mark.parametrize("before,after", [(5, 4), (4, 3), (10, 6), (3, 8)])
def test_no_event_otherwise(before, after):
    check_low_stock("EL-200", before, after)
    assert events.history("inventory.low_stock") == []


def test_threshold_comes_from_config():
    config.set("inventory.low_stock_threshold", 10)
    check_low_stock("EL-200", 11, 10)
    assert len(events.history("inventory.low_stock")) == 1


def test_reserving_raises_the_event_once_per_crossing():
    add_product(Product("EL-200", "Headphones", "electronics", Decimal("120.00"), 300))
    set_on_hand("EL-200", 8)
    reserve("ORD-1", [("EL-200", 3)])
    reserve("ORD-2", [("EL-200", 1)])
    assert len(events.history("inventory.low_stock")) == 1

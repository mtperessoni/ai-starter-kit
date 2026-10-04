"""Tests for volume_breaks (PRC-03, PRC-05)."""
from decimal import Decimal

import pytest

from market.features.pricing.volume_breaks import volume_discount, volume_percent
from market.infra import config


@pytest.mark.parametrize("qty,expected", [
    (1, "0"), (9, "0"), (10, "5"), (49, "5"), (50, "10"), (99, "10"),
])
def test_percent_by_quantity(qty, expected):
    assert volume_percent(qty) == Decimal(expected)


def test_gift_cards_never_get_a_break():
    assert volume_percent(60, "gift_card") == Decimal("0")
    assert volume_discount(Decimal("50.00"), 60, "gift_card") == Decimal("0.00")


def test_discount_is_rounded_half_up_to_cents():
    assert volume_discount(Decimal("1.11"), 10) == Decimal("0.56")
    assert volume_discount(Decimal("15.00"), 10) == Decimal("7.50")


def test_tiers_come_from_config():
    config.set("pricing.volume_tier1_qty", 3)
    config.set("pricing.volume_tier1_percent", Decimal("20"))
    assert volume_percent(3) == Decimal("20")
    assert volume_discount(Decimal("10.00"), 3) == Decimal("6.00")

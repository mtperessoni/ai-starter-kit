"""Tests for points_earning (LOY-01, LOY-02)."""
from decimal import Decimal

from market.features.loyalty.points_earning import explain_earning, points_for_order, tier_multiplier
from market.infra import config


def test_one_point_per_whole_currency_unit():
    assert points_for_order(Decimal("120.00"), "standard") == 120


def test_vip_earns_double():
    assert points_for_order(Decimal("120.00"), "vip") == 240


def test_only_whole_units_count():
    assert points_for_order(Decimal("108.99"), "standard") == 108
    assert points_for_order(Decimal("0.99"), "standard") == 0


def test_nothing_earns_nothing():
    assert points_for_order(Decimal("0.00"), "vip") == 0
    assert points_for_order(Decimal("-5.00"), "standard") == 0


def test_vip_multiplier_follows_config():
    config.set("loyalty.vip_multiplier", 3)
    assert tier_multiplier("vip") == 3 and tier_multiplier("standard") == 1


def test_explain_earning_shows_base_multiplier_and_result():
    assert explain_earning(Decimal("120.00"), "vip") == "120 x2 = 240 points"
    assert explain_earning(Decimal("108.99"), "standard") == "108 x1 = 108 points"

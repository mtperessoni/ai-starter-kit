"""Tests for discount_allocation (PRC-04, PRC-06)."""
from decimal import Decimal

from market.features.pricing.discount_allocation import line_discount_map
from market.features.promotions.promotion_models import AppliedDiscount


def D(value):
    return Decimal(value)


def test_no_discounts_gives_empty_map():
    assert line_discount_map([]) == {}


def test_sums_amounts_per_sku_across_discounts():
    discounts = [
        AppliedDiscount("A", "volume", D("5.00"), (("X", D("5.00")),)),
        AppliedDiscount("B", "percent_coupon", D("3.00"), (("X", D("2.00")), ("Y", D("1.00")))),
    ]
    assert line_discount_map(discounts) == {"X": D("7.00"), "Y": D("1.00")}


def test_skus_without_a_discount_are_absent():
    discounts = [AppliedDiscount("A", "bogo", D("1.00"), (("X", D("1.00")),))]
    assert "Z" not in line_discount_map(discounts)

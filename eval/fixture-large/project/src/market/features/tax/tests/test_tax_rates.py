"""Tests for tax_rates (TAX-01)."""
from decimal import Decimal

import pytest

from market.features.tax.tax_rates import DEFAULT_RATE, RATES, known_regions, rate_for, rate_label


@pytest.mark.parametrize("region,rate", [("SP", "8"), ("RJ", "10"), ("MG", "9")])
def test_listed_regions_have_their_rate(region, rate):
    assert rate_for(region) == Decimal(rate)


@pytest.mark.parametrize("region", ["ES", "AM", "BA"])
def test_other_regions_pay_the_default_rate(region):
    assert rate_for(region) == Decimal("7")


def test_missing_region_pays_the_default_rate():
    assert rate_for(None) == DEFAULT_RATE


def test_region_is_trimmed_and_case_insensitive():
    assert rate_for(" rj ") == Decimal("10")


def test_rates_table_has_three_regions():
    assert sorted(RATES) == ["MG", "RJ", "SP"]


def test_known_regions_are_sorted():
    assert known_regions() == ("MG", "RJ", "SP")


def test_rate_label_names_the_region_or_the_default():
    assert rate_label("SP") == "8% (SP)" and rate_label(" rj ") == "10% (RJ)"
    assert rate_label("AM") == "7% (default)" and rate_label(None) == "7% (default)"

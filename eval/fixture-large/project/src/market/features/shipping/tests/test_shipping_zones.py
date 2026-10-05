"""Tests for shipping_zones (SHP-01, SHP-06)."""
from decimal import Decimal

import pytest

from market.features.shipping.shipping_zones import (BASE_FEE, EXPRESS_DAYS, STANDARD_DAYS, base_fee,
                                                     delivery_days, regions_in_zone, zone_for, zone_summary)


def test_sao_paulo_is_zone_1():
    assert zone_for("SP") == 1


@pytest.mark.parametrize("region", ["RJ", "MG", "ES"])
def test_neighbour_states_are_zone_2(region):
    assert zone_for(region) == 2


@pytest.mark.parametrize("region", ["AM", "BA", "RS"])
def test_other_regions_are_zone_3(region):
    assert zone_for(region) == 3


def test_missing_region_is_zone_3():
    assert zone_for(None) == 3


def test_region_is_trimmed_and_case_insensitive():
    assert zone_for(" sp ") == 1


def test_base_fees_by_zone():
    assert [base_fee(z) for z in (1, 2, 3)] == [Decimal("10.00"), Decimal("18.00"), Decimal("30.00")]
    assert BASE_FEE[1] == Decimal("10.00")


def test_unknown_zone_is_an_error():
    with pytest.raises(KeyError):
        base_fee(9)
    with pytest.raises(KeyError):
        delivery_days(9, "standard")


def test_delivery_days_standard_and_express():
    assert [delivery_days(z, "standard") for z in (1, 2, 3)] == [3, 5, 8]
    assert [delivery_days(z, "express") for z in (1, 2, 3)] == [1, 2, 4]
    assert STANDARD_DAYS[3] == 8 and EXPRESS_DAYS[3] == 4


def test_regions_in_a_zone_are_listed_and_zone_3_is_open_ended():
    assert regions_in_zone(1) == ("SP",) and regions_in_zone(2) == ("ES", "MG", "RJ")
    assert regions_in_zone(3) == ()


def test_zone_summary_has_one_line_per_zone():
    rows = zone_summary()
    assert rows[0] == "zone 1: SP, 10.00, standard 3 days, express 1 day"
    assert rows[2] == "zone 3: other regions, 30.00, standard 8 days, express 4 days"

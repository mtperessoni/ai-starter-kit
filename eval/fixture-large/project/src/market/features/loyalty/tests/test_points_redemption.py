"""Tests for points_redemption (LOY-04): value, steps, balance and the 50% limit."""
from decimal import Decimal

import pytest

from market.features.loyalty.points_ledger import add_points
from market.features.loyalty.points_redemption import (LoyaltyRedemptionPort, max_redeemable_points,
                                                         redemption_value)
from market.infra import config
from market.infra.errors import PolicyError, ValidationError

MERCH = Decimal("200.00")


@pytest.fixture(autouse=True)
def balance_of_2000():
    add_points("C-1", 2000, "grant")


def test_100_points_are_worth_1_00():
    assert redemption_value("C-1", 500, MERCH) == Decimal("5.00")
    assert redemption_value("C-1", 1200, MERCH) == Decimal("12.00")


def test_zero_points_are_worth_nothing():
    assert redemption_value("C-1", 0, MERCH) == Decimal("0.00")


def test_points_must_be_a_multiple_of_100():
    with pytest.raises(ValidationError):
        redemption_value("C-1", 550, MERCH)


def test_at_least_500_points_at_a_time():
    with pytest.raises(ValidationError):
        redemption_value("C-1", 400, MERCH)


def test_negative_points_are_invalid():
    with pytest.raises(ValidationError):
        redemption_value("C-1", -500, MERCH)


def test_points_above_the_balance_are_refused():
    with pytest.raises(PolicyError) as error:
        redemption_value("C-1", 2100, Decimal("10000.00"))
    assert error.value.reason == "insufficient_points"


def test_value_is_capped_at_half_the_merchandise():
    assert redemption_value("C-1", 600, Decimal("12.00")) == Decimal("6.00")
    with pytest.raises(PolicyError) as error:
        redemption_value("C-1", 700, Decimal("12.00"))
    assert error.value.reason == "redeem_limit"


def test_the_minimum_follows_config():
    config.set("loyalty.redeem_min_points", 100)
    assert redemption_value("C-1", 100, MERCH) == Decimal("1.00")


def test_the_port_delegates_to_the_function():
    assert LoyaltyRedemptionPort().redemption_value("C-1", 500, MERCH) == Decimal("5.00")


def test_max_redeemable_points_respects_balance_step_and_cap():
    assert max_redeemable_points("C-1", Decimal("10000.00")) == 2000
    assert max_redeemable_points("C-1", Decimal("12.00")) == 600
    assert max_redeemable_points("C-1", Decimal("200.00")) == 2000


def test_max_redeemable_points_is_zero_below_the_minimum():
    assert max_redeemable_points("C-1", Decimal("8.00")) == 0
    assert max_redeemable_points("C-2", Decimal("200.00")) == 0

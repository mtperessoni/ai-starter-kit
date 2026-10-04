"""Tests for installments (PAY-02): interest, rounding, limits."""
from decimal import Decimal

import pytest

from market.features.payments.installments import (check_minimum_installment, installment_options,
                                                   installment_plan, interest_for)
from market.infra import config
from market.infra.errors import ValidationError


def test_one_installment_has_no_interest():
    assert installment_plan(Decimal("100.00"), 1) == (Decimal("100.00"), Decimal("100.00"))


def test_interest_is_per_extra_installment():
    assert interest_for(Decimal("100.00"), 3) == Decimal("3.98")
    assert installment_plan(Decimal("100.00"), 3) == (Decimal("103.98"), Decimal("34.66"))


def test_six_installments_round_half_up():
    assert installment_plan(Decimal("120.00"), 6) == (Decimal("131.94"), Decimal("21.99"))


@pytest.mark.parametrize("count", [0, 7, -1])
def test_installments_outside_one_to_six_are_invalid(count):
    with pytest.raises(ValidationError):
        installment_plan(Decimal("100.00"), count)


def test_maximum_follows_config():
    config.set("payments.max_installments", 12)
    assert installment_plan(Decimal("120.00"), 12)[0] == Decimal("146.27")


def test_amount_must_be_positive():
    with pytest.raises(ValidationError):
        installment_plan(Decimal("0.00"), 1)


def test_each_installment_must_reach_the_minimum():
    check_minimum_installment(Decimal("10.00"), 3)
    with pytest.raises(ValidationError):
        check_minimum_installment(Decimal("9.99"), 3)


def test_minimum_does_not_apply_to_a_single_installment():
    check_minimum_installment(Decimal("5.00"), 1)


def test_options_stop_when_installments_fall_below_the_minimum():
    options = installment_options(Decimal("40.00"))
    assert [count for count, _, _ in options] == [1, 2, 3, 4]
    assert installment_options(Decimal("15.00")) == [(1, Decimal("15.00"), Decimal("15.00"))]


def test_options_offer_all_six_plans_for_a_large_amount():
    assert [count for count, _, _ in installment_options(Decimal("600.00"))] == [1, 2, 3, 4, 5, 6]

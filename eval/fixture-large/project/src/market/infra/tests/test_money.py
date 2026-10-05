"""Tests for infra.money (PRC-04 allocation, half-up rounding rules)."""
from decimal import Decimal

import pytest

from market.infra.money import D, allocate, pct, q2


@pytest.mark.parametrize("raw,expected", [
    ("1.005", "1.01"), ("1.004", "1.00"), ("2.675", "2.68"), ("0.125", "0.13"), ("10", "10.00"),
])
def test_q2_rounds_half_up(raw, expected):
    assert q2(Decimal(raw)) == Decimal(expected)


def test_d_builds_from_str_not_float():
    assert D(0.1) == Decimal("0.1")
    assert D("12.50") == Decimal("12.50")
    assert D(3) == Decimal("3")


def test_pct_is_unrounded():
    assert pct(Decimal("33.33"), Decimal("10")) == Decimal("3.333")


def test_allocate_sums_exactly_with_remainder_on_last():
    parts = allocate(Decimal("10.00"), [Decimal("1"), Decimal("1"), Decimal("1")])
    assert parts == [Decimal("3.33"), Decimal("3.33"), Decimal("3.34")]
    assert sum(parts) == Decimal("10.00")


def test_allocate_remainder_goes_to_last_positive_weight():
    parts = allocate(Decimal("5.00"), [Decimal("1"), Decimal("1"), Decimal("0")])
    assert parts == [Decimal("2.50"), Decimal("2.50"), Decimal("0.00")]


def test_allocate_all_zero_weights_gives_zeros():
    assert allocate(Decimal("5.00"), [Decimal("0"), Decimal("0")]) == [Decimal("0.00"), Decimal("0.00")]

"""Tests for points_ledger (LOY-05, LOY-06): lots, FIFO, expiry, claw-back."""
import pytest

from market.features.loyalty.points_ledger import (add_points, balance, claw_back, expire_lots, expiring_points,
                                                        lifetime_points, lots_of, points_summary, spend)
from market.infra import clock
from market.infra.errors import PolicyError, ValidationError


def test_points_are_added_as_lots():
    add_points("C-1", 300, "grant")
    add_points("C-1", 200, "grant")
    assert balance("C-1") == 500 and balance("C-2") == 0


def test_spending_takes_the_oldest_points_first():
    add_points("C-1", 300, "grant")
    clock.advance(days=1)
    add_points("C-1", 400, "grant")
    spend("C-1", 500)
    assert balance("C-1") == 200
    clock.advance(days=364)
    assert balance("C-1") == 200


def test_spending_more_than_the_balance_changes_nothing():
    add_points("C-1", 300, "grant")
    with pytest.raises(PolicyError) as error:
        spend("C-1", 301)
    assert error.value.reason == "insufficient_points" and balance("C-1") == 300


def test_spending_zero_is_invalid():
    with pytest.raises(ValidationError):
        spend("C-1", 0)


def test_points_expire_365_days_after_they_were_earned():
    add_points("C-1", 300, "grant")
    clock.advance(days=364)
    assert balance("C-1") == 300
    clock.advance(days=1)
    assert balance("C-1") == 0


def test_expired_points_cannot_be_spent():
    add_points("C-1", 300, "grant")
    clock.advance(days=400)
    with pytest.raises(PolicyError):
        spend("C-1", 100)


def test_expire_lots_reports_the_points_removed():
    add_points("C-1", 300, "grant")
    clock.advance(days=200)
    add_points("C-1", 100, "grant")
    clock.advance(days=170)
    assert expire_lots("C-1") == 300
    assert expire_lots("C-1") == 0 and balance("C-1") == 100


def test_claw_back_floors_at_zero():
    add_points("C-1", 100, "grant")
    assert claw_back("C-1", 250) == 100
    assert balance("C-1") == 0


def test_claw_back_takes_the_newest_points_first():
    add_points("C-1", 100, "grant")
    clock.advance(days=1)
    add_points("C-1", 100, "order:ORD-0001")
    assert claw_back("C-1", 100) == 100
    clock.advance(days=364)
    assert balance("C-1") == 0 and claw_back("C-1", 0) == 0


def test_adding_needs_positive_points_and_a_reason():
    with pytest.raises(ValidationError):
        add_points("C-1", 0, "grant")
    with pytest.raises(ValidationError):
        add_points("C-1", 10, " ")


def test_lots_of_lists_live_lots_oldest_first():
    add_points("C-1", 100, "grant")
    clock.advance(days=1)
    add_points("C-1", 200, "order:ORD-0001")
    assert [lot.points for lot in lots_of("C-1")] == [100, 200]
    clock.advance(days=365)
    assert lots_of("C-1") == []


def test_expiring_points_counts_lots_within_the_horizon():
    add_points("C-1", 100, "grant")
    clock.advance(days=350)
    add_points("C-1", 200, "grant")
    assert expiring_points("C-1", 30) == 100 and expiring_points("C-1", 400) == 300
    with pytest.raises(ValidationError):
        expiring_points("C-1", -1)


def test_lifetime_points_include_spent_and_expired_points():
    add_points("C-1", 100, "grant")
    add_points("C-1", 300, "grant")
    spend("C-1", 400)
    assert balance("C-1") == 0 and lifetime_points("C-1") == 400


def test_points_summary_combines_balance_expiry_and_lifetime():
    add_points("C-1", 100, "grant")
    clock.advance(days=350)
    add_points("C-1", 400, "grant")
    spend("C-1", 50)
    assert points_summary("C-1") == {"balance": 450, "expiring_30_days": 50, "lifetime": 500}

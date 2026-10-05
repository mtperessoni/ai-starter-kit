"""Tests for promotion_usage (PRM-04: held, committed, released)."""
from market.features.promotions.promotion_usage import (commit_uses, hold_uses, release_uses,
                                                        usage_count)


def test_held_use_counts():
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    assert usage_count("SAVE20") == 1
    assert usage_count("SAVE20", "C-1") == 1
    assert usage_count("SAVE20", "C-2") == 0


def test_committed_use_still_counts():
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    commit_uses("ORD-1")
    assert usage_count("SAVE20", "C-1") == 1


def test_release_gives_the_use_back():
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    release_uses("ORD-1")
    assert usage_count("SAVE20", "C-1") == 0


def test_release_is_idempotent_and_ignores_unknown_orders():
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    release_uses("ORD-1")
    release_uses("ORD-1")
    release_uses("ORD-X")
    assert usage_count("SAVE20") == 0


def test_a_committed_use_cannot_be_released():
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    commit_uses("ORD-1")
    release_uses("ORD-1")
    assert usage_count("SAVE20") == 1


def test_codes_are_normalized_and_counted_per_order_once():
    hold_uses("ORD-1", "C-1", [" save20 ", "SAVE20"])
    hold_uses("ORD-2", "C-2", ["SAVE20", "FIX15"])
    assert usage_count("save20") == 2
    assert usage_count("FIX15") == 1

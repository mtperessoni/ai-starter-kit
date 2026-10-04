"""Tests for infra.ids (ORD-0001 style ids used by CHK, INV, CRT rules)."""
from market.infra import ids


def test_ids_are_four_digit_and_counted_per_prefix():
    assert ids.next_id("ORD") == "ORD-0001"
    assert ids.next_id("ORD") == "ORD-0002"
    assert ids.next_id("PAY") == "PAY-0001"


def test_reset_restarts_counters():
    ids.next_id("RSV")
    ids.reset()
    assert ids.next_id("RSV") == "RSV-0001"

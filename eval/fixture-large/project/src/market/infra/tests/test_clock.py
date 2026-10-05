"""Tests for infra.clock (time travel used by CRT-07, INV-04, LOY-05, RET-01)."""
from datetime import date, datetime

from market.infra import clock


def test_default_clock_is_demo_time():
    assert clock.now() == datetime(2026, 3, 10, 12, 0)
    assert clock.today() == date(2026, 3, 10)


def test_set_now_and_advance():
    clock.set_now(datetime(2026, 1, 1, 8, 0))
    assert clock.advance(days=1, hours=2, minutes=30) == datetime(2026, 1, 2, 10, 30)
    assert clock.now() == datetime(2026, 1, 2, 10, 30)


def test_reset_restores_default():
    clock.advance(days=40)
    clock.reset()
    assert clock.now() == datetime(2026, 3, 10, 12, 0)

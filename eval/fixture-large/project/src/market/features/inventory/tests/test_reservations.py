"""Tests for reservations (INV-02, INV-03, INV-04, INV-05, INV-06, INV-07)."""
from datetime import datetime
from decimal import Decimal

import pytest

from market.features.catalog.product_store import add_product
from market.features.inventory.reservations import (commit, expire_due, get_reservation, release,
                                                    reserve)
from market.features.inventory.stock_store import available, on_hand, set_on_hand
from market.infra import clock, config
from market.infra.errors import NotFoundError, OutOfStockError, PolicyError, ValidationError
from market.infra.models import Product


@pytest.fixture(autouse=True)
def catalog():
    add_product(Product("BK-100", "Python Basics", "books", Decimal("40.00"), 400))
    add_product(Product("EL-200", "Headphones", "electronics", Decimal("120.00"), 300))
    add_product(Product("GC-050", "Gift Card 50", "gift_card", Decimal("50.00"), 0))
    set_on_hand("BK-100", 10)
    set_on_hand("EL-200", 5)


def test_reserve_holds_stock_for_thirty_minutes():
    held = reserve("ORD-1", [("EL-200", 2)])
    assert held.reservation_id == "RSV-0001" and held.status == "active"
    assert held.expires_at == datetime(2026, 3, 10, 12, 30)
    assert available("EL-200") == 3 and on_hand("EL-200") == 5


def test_reserve_is_all_or_nothing_and_names_every_short_sku():
    with pytest.raises(OutOfStockError) as caught:
        reserve("ORD-1", [("BK-100", 11), ("EL-200", 6)])
    assert caught.value.skus == ("BK-100", "EL-200")
    assert available("BK-100") == 10 and available("EL-200") == 5


def test_a_line_that_fits_is_not_named_when_another_is_short():
    with pytest.raises(OutOfStockError) as caught:
        reserve("ORD-1", [("BK-100", 1), ("EL-200", 6)])
    assert caught.value.skus == ("EL-200",) and available("BK-100") == 10


def test_duplicate_lines_are_merged_before_checking():
    held = reserve("ORD-1", [("EL-200", 3), ("EL-200", 2)])
    assert held.lines == (("EL-200", 5),) and available("EL-200") == 0
    with pytest.raises(OutOfStockError):
        reserve("ORD-2", [("EL-200", 1)])


def test_bad_quantity_or_empty_reservation_is_invalid():
    with pytest.raises(ValidationError):
        reserve("ORD-1", [("EL-200", 0)])
    with pytest.raises(ValidationError):
        reserve("ORD-1", [])


def test_gift_cards_are_never_held():
    held = reserve("ORD-1", [("GC-050", 3), ("EL-200", 1)])
    assert available("GC-050") == 10**9
    commit(held.reservation_id)
    assert on_hand("EL-200") == 4


def test_reservation_expires_after_thirty_minutes():
    reserve("ORD-1", [("EL-200", 2)])
    clock.advance(minutes=29)
    assert expire_due() == 0 and available("EL-200") == 3
    clock.advance(minutes=1)
    assert available("EL-200") == 5
    assert expire_due() == 1
    assert get_reservation("RSV-0001").status == "expired"
    assert expire_due() == 0


def test_expiry_minutes_come_from_config():
    config.set("inventory.reservation_minutes", 5)
    held = reserve("ORD-1", [("EL-200", 1)])
    assert held.expires_at == datetime(2026, 3, 10, 12, 5)


def test_release_gives_stock_back():
    held = reserve("ORD-1", [("EL-200", 2)])
    assert release(held.reservation_id).status == "released"
    assert available("EL-200") == 5


def test_release_twice_changes_nothing():
    held = reserve("ORD-1", [("EL-200", 2)])
    release(held.reservation_id)
    reserve("ORD-2", [("EL-200", 3)])
    assert release(held.reservation_id).status == "released"
    assert available("EL-200") == 2


def test_commit_removes_stock_and_ends_the_hold():
    held = reserve("ORD-1", [("EL-200", 2)])
    assert commit(held.reservation_id).status == "committed"
    assert on_hand("EL-200") == 3 and available("EL-200") == 3


def test_released_reservation_cannot_be_committed():
    held = reserve("ORD-1", [("EL-200", 2)])
    release(held.reservation_id)
    with pytest.raises(PolicyError):
        commit(held.reservation_id)
    assert on_hand("EL-200") == 5


def test_expired_reservation_cannot_be_committed_even_before_the_sweep():
    held = reserve("ORD-1", [("EL-200", 2)])
    clock.advance(minutes=31)
    with pytest.raises(PolicyError):
        commit(held.reservation_id)
    assert on_hand("EL-200") == 5


def test_releasing_a_committed_reservation_changes_nothing():
    held = reserve("ORD-1", [("EL-200", 2)])
    commit(held.reservation_id)
    assert release(held.reservation_id).status == "committed"
    assert on_hand("EL-200") == 3


def test_unknown_reservation_raises_not_found():
    with pytest.raises(NotFoundError):
        get_reservation("RSV-9999")

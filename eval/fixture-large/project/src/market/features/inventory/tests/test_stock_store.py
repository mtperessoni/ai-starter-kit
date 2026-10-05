"""Tests for stock_store (INV-01, INV-02, INV-07, INV-08)."""
from decimal import Decimal

import pytest

from market.features.catalog.product_store import add_product
from market.features.inventory.reservations import reserve, release
from market.features.inventory.stock_store import add_stock, available, on_hand, reserved, set_on_hand
from market.infra import events
from market.infra.errors import NotFoundError, ValidationError
from market.infra.models import Product


@pytest.fixture(autouse=True)
def catalog():
    add_product(Product("EL-200", "Headphones", "electronics", Decimal("120.00"), 300))
    add_product(Product("GC-050", "Gift Card 50", "gift_card", Decimal("50.00"), 0))


def test_set_and_read_on_hand():
    set_on_hand("EL-200", 5)
    assert on_hand("EL-200") == 5 and available("EL-200") == 5


def test_untouched_sku_has_zero_on_hand():
    assert on_hand("EL-200") == 0 and available("EL-200") == 0


def test_stock_cannot_be_negative():
    with pytest.raises(ValidationError):
        set_on_hand("EL-200", -1)


def test_unknown_sku_raises_not_found():
    with pytest.raises(NotFoundError):
        set_on_hand("NOPE-1", 1)
    with pytest.raises(NotFoundError):
        available("NOPE-1")


def test_available_is_on_hand_minus_active_reservations():
    set_on_hand("EL-200", 5)
    reserve("ORD-1", [("EL-200", 2)])
    assert reserved("EL-200") == 2 and available("EL-200") == 3


def test_released_reservation_no_longer_counts():
    set_on_hand("EL-200", 5)
    held = reserve("ORD-1", [("EL-200", 2)])
    release(held.reservation_id)
    assert reserved("EL-200") == 0 and available("EL-200") == 5


def test_gift_cards_are_always_available():
    assert available("GC-050") == 10**9
    set_on_hand("GC-050", 0)
    assert available("GC-050") == 10**9


def test_add_stock_returns_new_on_hand():
    set_on_hand("EL-200", 2)
    assert add_stock("EL-200", 3) == 5


def test_add_stock_needs_a_positive_quantity():
    with pytest.raises(ValidationError):
        add_stock("EL-200", 0)


def test_restocked_event_when_nothing_was_available():
    add_stock("EL-200", 3)
    event = events.history("inventory.restocked")[0]
    assert event.payload == {"sku": "EL-200", "available": 3}


def test_no_restocked_event_when_stock_was_available():
    set_on_hand("EL-200", 2)
    add_stock("EL-200", 3)
    assert events.history("inventory.restocked") == []


def test_restocked_event_when_everything_was_reserved():
    set_on_hand("EL-200", 2)
    reserve("ORD-1", [("EL-200", 2)])
    add_stock("EL-200", 4)
    assert len(events.history("inventory.restocked")) == 1


def test_no_restocked_event_for_gift_cards():
    add_stock("GC-050", 5)
    assert events.history("inventory.restocked") == []

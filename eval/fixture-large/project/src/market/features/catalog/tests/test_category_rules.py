"""Tests for category_rules (CAT-03, PRC-05, INV-07, RET-02)."""
import pytest

from market.features.catalog.category_rules import (CATEGORIES, EXEMPT_CATEGORIES, is_digital,
                                                    is_returnable, is_stock_tracked)


def test_categories_and_exempt_set():
    assert len(CATEGORIES) == 7
    assert set(EXEMPT_CATEGORIES) == {"books", "grocery", "gift_card"}


def test_only_gift_card_is_digital_and_untracked():
    assert is_digital("gift_card") and not is_digital("books")
    assert not is_stock_tracked("gift_card") and is_stock_tracked("grocery")


@pytest.mark.parametrize("category,expected", [
    ("gift_card", False), ("grocery", False), ("books", True), ("toys", True),
])
def test_returnable(category, expected):
    assert is_returnable(category) is expected

"""Tests for infra.config (every rule whose change goes via config)."""
from decimal import Decimal

import pytest

from market.infra import config


def test_defaults_are_readable():
    assert config.get("cart.max_qty") == 99
    assert config.get("promo.max_total_discount_percent") == Decimal("40")


def test_set_overrides_and_reset_restores():
    config.set("cart.max_qty", 5)
    assert config.get("cart.max_qty") == 5
    config.reset()
    assert config.get("cart.max_qty") == 99


def test_unknown_key_raises_key_error():
    with pytest.raises(KeyError):
        config.get("no.such.key")
    with pytest.raises(KeyError):
        config.set("no.such.key", 1)

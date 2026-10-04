"""Tests for quote_models (PRC-01, PRC-02, PRC-06 data shapes)."""
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from market.features.pricing.quote_models import LineQuote, PriceQuote


def test_quote_models_hold_the_spec_fields():
    line = LineQuote("A-1", "toys", 2, Decimal("5.00"), Decimal("10.00"), Decimal("0"),
                     Decimal("10.00"), "standard", 100)
    quote = PriceQuote((line,), Decimal("10.00"), (), Decimal("0"), Decimal("10.00"), False, ())
    assert quote.lines[0].sku == "A-1" and quote.rejected_coupons == ()


def test_quotes_are_immutable():
    quote = PriceQuote((), Decimal("0"), (), Decimal("0"), Decimal("0"), False, ())
    with pytest.raises(FrozenInstanceError):
        quote.total = Decimal("1")  # type: ignore[misc]

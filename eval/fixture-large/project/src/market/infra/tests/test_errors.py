"""Tests for infra.errors (the error codes every rule raises)."""
from market.infra.errors import (MarketError, NotFoundError, OutOfStockError,
                                 PolicyError, ValidationError)


def test_codes():
    assert NotFoundError("x").code == "not_found"
    assert ValidationError("x").code == "invalid"
    assert OutOfStockError("x").code == "out_of_stock"
    assert PolicyError("why").code == "policy"


def test_out_of_stock_carries_skus_and_policy_carries_reason():
    err = OutOfStockError("short", ("A-1", "B-2"))
    assert err.skus == ("A-1", "B-2")
    pol = PolicyError("not_verified_buyer")
    assert pol.reason == "not_verified_buyer" and str(pol) == "not_verified_buyer"


def test_all_are_market_errors():
    for cls in (NotFoundError, ValidationError, OutOfStockError):
        assert issubclass(cls, MarketError)
    assert issubclass(PolicyError, MarketError)

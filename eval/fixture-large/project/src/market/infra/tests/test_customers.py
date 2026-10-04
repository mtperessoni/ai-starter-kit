"""Tests for infra.customers (tiers and regions behind SHP-03, TAX-01, LOY-02)."""
import pytest

from market.infra.customers import add_customer, get_customer
from market.infra.errors import NotFoundError, ValidationError
from market.infra.models import Customer


def test_add_and_get_customer():
    add_customer(Customer("C-1", "one@example.com", "vip", "RJ"))
    got = get_customer("C-1")
    assert (got.tier, got.region, got.tax_exempt) == ("vip", "RJ", False)


def test_unknown_customer_raises_not_found():
    with pytest.raises(NotFoundError):
        get_customer("C-X")


def test_bad_tier_and_duplicate_are_rejected():
    with pytest.raises(ValidationError):
        add_customer(Customer("C-2", "two@example.com", "gold"))
    add_customer(Customer("C-3", "three@example.com"))
    with pytest.raises(ValidationError):
        add_customer(Customer("C-3", "three@example.com"))

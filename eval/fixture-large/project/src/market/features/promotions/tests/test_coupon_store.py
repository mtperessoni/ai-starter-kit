"""Tests for coupon_store (PRM-01, PRM-02, PRM-07, PRM-08, PRM-09)."""
from datetime import date
from decimal import Decimal

import pytest

from market.features.promotions.coupon_store import (active_sales, add_bogo, add_bundle,
                                                     add_category_sale, add_coupon, bogo_rules,
                                                     bundles, find_coupon, get_coupon,
                                                     normalize_code)
from market.features.promotions.promotion_models import BogoRule, Bundle, CategorySale, Coupon
from market.infra.errors import NotFoundError, ValidationError


def test_normalize_code_strips_and_uppercases():
    assert normalize_code("  save10 ") == "SAVE10"


def test_add_coupon_normalizes_the_stored_code():
    stored = add_coupon(Coupon(" save10 ", "percent", Decimal("10")))
    assert stored.code == "SAVE10"
    assert get_coupon("Save10").code == "SAVE10"


def test_duplicate_coupon_rejected_even_with_other_case():
    add_coupon(Coupon("SAVE10", "percent", Decimal("10")))
    with pytest.raises(ValidationError):
        add_coupon(Coupon("save10", "percent", Decimal("10")))


@pytest.mark.parametrize("value", ["0", "-5", "100.01"])
def test_percent_outside_range_rejected(value):
    with pytest.raises(ValidationError):
        add_coupon(Coupon("BAD", "percent", Decimal(value)))


def test_percent_100_is_allowed():
    assert add_coupon(Coupon("FULL", "percent", Decimal("100"))).value == Decimal("100")


def test_unknown_kind_and_bad_fixed_rejected():
    with pytest.raises(ValidationError):
        add_coupon(Coupon("BAD", "bonus", Decimal("1")))
    with pytest.raises(ValidationError):
        add_coupon(Coupon("BAD2", "fixed", Decimal("0")))


def test_get_unknown_raises_and_find_returns_none():
    with pytest.raises(NotFoundError):
        get_coupon("NOPE")
    assert find_coupon("NOPE") is None


def test_active_sales_filters_by_date_inclusive():
    add_category_sale(CategorySale("S1", "toys", Decimal("20"), date(2026, 3, 1), date(2026, 3, 31)))
    assert [s.sale_id for s in active_sales(date(2026, 3, 31))] == ["S1"]
    assert active_sales(date(2026, 4, 1)) == []
    assert active_sales(date(2026, 2, 28)) == []


def test_bogo_and_bundle_registration():
    add_bogo(BogoRule("B1", "FS-100"))
    add_bundle(Bundle("U1", ("BK-100", "BK-200"), Decimal("15.00")))
    assert [r.rule_id for r in bogo_rules()] == ["B1"]
    assert [b.bundle_id for b in bundles()] == ["U1"]


def test_bad_bundle_and_sale_rejected():
    with pytest.raises(ValidationError):
        add_bundle(Bundle("U2", ("BK-100",), Decimal("15.00")))
    with pytest.raises(ValidationError):
        add_category_sale(CategorySale("S2", "toys", Decimal("20"), date(2026, 3, 31), date(2026, 3, 1)))

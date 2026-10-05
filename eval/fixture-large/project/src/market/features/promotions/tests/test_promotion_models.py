"""Tests for promotion_models (PRM-01 to PRM-13 data shapes)."""
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from market.features.promotions.promotion_models import (BogoRule, Coupon, PromoResult)


def test_coupon_defaults():
    coupon = Coupon("X", "percent", Decimal("10"))
    assert coupon.min_subtotal == Decimal("0") and coupon.categories == ()
    assert coupon.per_customer_limit is None and coupon.expires_on is None


def test_bogo_defaults_are_buy_two_get_one():
    rule = BogoRule("R", "FS-100")
    assert (rule.buy, rule.free) == (2, 1)


def test_models_are_frozen():
    with pytest.raises(FrozenInstanceError):
        Coupon("X", "percent", Decimal("10")).code = "Y"  # type: ignore[misc]


def test_promo_result_holds_everything_pricing_needs():
    result = PromoResult((), Decimal("0.00"), False, (), ())
    assert result.total == 0 and result.rejected == () and result.applied_codes == ()
    assert date(2026, 3, 10).year == 2026

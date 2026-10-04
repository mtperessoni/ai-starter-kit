"""Tests for shipping_fee (SHP-01 to SHP-06)."""
from datetime import date
from decimal import Decimal

import pytest

from market.features.pricing.quote_models import LineQuote
from market.features.shipping.shipping_fee import (ShippingRequest, describe_shipping, estimated_delivery,
                                                      quote_shipping, shipping_options)
from market.infra import config
from market.infra.errors import PolicyError, ValidationError


def line(category="electronics", qty=1, weight=300, price="120.00", sku="EL-200"):
    unit = Decimal(price)
    return LineQuote(sku, category, qty, unit, unit * qty, Decimal("0.00"), unit * qty, "standard", weight)


def request(lines=None, region="SP", merchandise="120.00", tier="standard", method="standard", coupon=False):
    return ShippingRequest(region, lines if lines is not None else [line()], Decimal(merchandise),
                           tier, method, coupon)


def test_standard_to_sao_paulo():
    quote = quote_shipping(request())
    assert (quote.fee, quote.zone, quote.estimated_days, quote.free_reason) == (Decimal("10.00"), 1, 3, None)


def test_standard_to_rio_is_18():
    quote = quote_shipping(request(region="RJ"))
    assert quote.fee == Decimal("18.00") and quote.zone == 2 and quote.estimated_days == 5


def test_standard_to_other_region_is_30():
    quote = quote_shipping(request(region="AM"))
    assert quote.fee == Decimal("30.00") and quote.zone == 3 and quote.estimated_days == 8


def test_weight_surcharge_is_added():
    quote = quote_shipping(request([line(), line("home", 1, 1500, "80.00", "HM-100")], merchandise="199.99"))
    assert quote.fee == Decimal("16.00") and quote.total_weight_grams == 1800


def test_free_at_the_threshold():
    quote = quote_shipping(request(merchandise="200.00"))
    assert quote.fee == Decimal("0.00") and quote.free_reason == "threshold"


def test_not_free_one_cent_below_the_threshold():
    assert quote_shipping(request(merchandise="199.99")).fee == Decimal("10.00")


def test_vip_threshold_is_lower():
    assert quote_shipping(request(merchandise="100.00", tier="vip")).free_reason == "threshold"
    assert quote_shipping(request(merchandise="100.00", tier="standard")).free_reason is None


def test_free_shipping_coupon_waives_standard():
    quote = quote_shipping(request(coupon=True))
    assert quote.fee == Decimal("0.00") and quote.free_reason == "coupon"


def test_express_costs_one_and_a_half_times():
    quote = quote_shipping(request(method="express"))
    assert quote.fee == Decimal("15.00") and quote.estimated_days == 1


def test_express_in_zone_2_with_weight():
    quote = quote_shipping(request(region="RJ", method="express", lines=[line(weight=1800)]))
    assert quote.fee == Decimal("36.00") and quote.estimated_days == 2


def test_express_is_never_free():
    quote = quote_shipping(request(method="express", merchandise="500.00", coupon=True))
    assert quote.fee == Decimal("15.00") and quote.free_reason is None


def test_express_multiplier_follows_config():
    config.set("shipping.express_multiplier", Decimal("2"))
    assert quote_shipping(request(method="express")).fee == Decimal("20.00")


def test_gift_card_only_has_no_shipping():
    gift = [line("gift_card", 1, 0, "50.00", "GC-050")]
    quote = quote_shipping(request(gift, merchandise="50.00"))
    assert (quote.fee, quote.estimated_days, quote.free_reason) == (Decimal("0.00"), 0, "digital")


def test_express_is_not_offered_for_gift_cards_only():
    gift = [line("gift_card", 1, 0, "50.00", "GC-050")]
    with pytest.raises(PolicyError) as error:
        quote_shipping(request(gift, method="express"))
    assert error.value.reason == "express_not_available"


def test_gift_card_in_a_mixed_order_does_not_add_weight():
    mixed = [line("gift_card", 1, 50, "50.00", "GC-050"), line(weight=300)]
    assert quote_shipping(request(mixed)).total_weight_grams == 300


def test_over_30000_grams_is_refused():
    with pytest.raises(PolicyError) as error:
        quote_shipping(request([line(qty=2, weight=15001)]))
    assert error.value.reason == "weight_limit_exceeded"


def test_exactly_30000_grams_is_accepted():
    quote = quote_shipping(request([line(qty=2, weight=15000)]))
    assert quote.fee == Decimal("10.00") + Decimal("174.00")


def test_unknown_method_is_invalid():
    with pytest.raises(ValidationError):
        quote_shipping(request(method="drone"))


def test_missing_region_uses_the_far_zone():
    assert quote_shipping(request(region=None)).zone == 3


def test_options_offer_standard_and_express():
    options = shipping_options(request())
    assert sorted(options) == ["express", "standard"]
    assert (options["standard"].fee, options["express"].fee) == (Decimal("10.00"), Decimal("15.00"))


def test_options_for_gift_cards_only_offer_standard():
    gift = [line("gift_card", 1, 0, "50.00", "GC-050")]
    assert list(shipping_options(request(gift))) == ["standard"]


def test_options_still_raise_for_overweight_goods():
    with pytest.raises(PolicyError):
        shipping_options(request([line(qty=2, weight=15001)]))


def test_estimated_delivery_adds_the_zone_days():
    assert estimated_delivery(quote_shipping(request()), date(2026, 3, 10)) == date(2026, 3, 13)
    assert estimated_delivery(quote_shipping(request(method="express")), date(2026, 3, 10)) == date(2026, 3, 11)


def test_estimated_delivery_of_gift_cards_is_none():
    gift = [line("gift_card", 1, 0, "50.00", "GC-050")]
    assert estimated_delivery(quote_shipping(request(gift)), date(2026, 3, 10)) is None


def test_describe_shipping_is_one_line():
    assert describe_shipping(quote_shipping(request())) == "standard 10.00 to zone 1 in 3 days"
    assert describe_shipping(quote_shipping(request(merchandise="200.00"))) == (
        "standard 0.00 to zone 1 in 3 days (free: threshold)")
    gift = [line("gift_card", 1, 0, "50.00", "GC-050")]
    assert describe_shipping(quote_shipping(request(gift))) == "standard 0.00 (free: digital)"

"""SHP-01 to SHP-06: the shipping quote for a set of priced lines."""
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal

from market.features.pricing.quote_models import LineQuote
from market.features.shipping.shipping_rules import (free_threshold, is_digital_only, is_overweight,
                                                      total_weight, weight_surcharge)
from market.features.shipping.shipping_zones import base_fee, delivery_days, zone_for
from market.infra import config
from market.infra.errors import PolicyError, ValidationError
from market.infra.money import q2

METHODS = ("standard", "express")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ShippingRequest:
    region: str | None
    lines: Sequence[LineQuote]
    merchandise_total: Decimal
    customer_tier: str
    method: str = "standard"
    free_shipping_coupon: bool = False


@dataclass(frozen=True)
class ShippingQuote:
    fee: Decimal
    zone: int
    method: str
    estimated_days: int
    free_reason: str | None
    total_weight_grams: int


def _digital_quote(request: ShippingRequest) -> ShippingQuote:
    return ShippingQuote(ZERO, zone_for(request.region), request.method, 0, "digital", 0)


def _standard_fee(request: ShippingRequest, fee: Decimal) -> tuple[Decimal, str | None]:
    """Apply the threshold and coupon waivers; both apply to standard only (SHP-03, SHP-06)."""
    if request.merchandise_total >= free_threshold(request.customer_tier):
        return ZERO, "threshold"
    if request.free_shipping_coupon:
        return ZERO, "coupon"
    return fee, None


def quote_shipping(request: ShippingRequest) -> ShippingQuote:
    """Quote shipping for the request.

    Order of decisions:
      1. unknown method is a ValidationError;
      2. gift-card-only: fee 0.00, no days, free reason digital; express is not offered (SHP-05);
      3. more than 30000 g of physical goods is refused (SHP-06);
      4. fee = zone base + weight surcharge (SHP-01, SHP-02);
      5. standard: waived by threshold or coupon; express: 1.5 times the fee, never free (SHP-05).

    Example: SP, 1800 g, merchandise 199.99, standard gives 16.00; the same cart express gives 24.00.
    """
    if request.method not in METHODS:
        raise ValidationError(f"unknown shipping method {request.method}")
    if is_digital_only(request.lines):
        if request.method == "express":
            raise PolicyError("express_not_available")
        return _digital_quote(request)
    grams = total_weight(request.lines)
    if is_overweight(grams):
        raise PolicyError("weight_limit_exceeded")
    zone = zone_for(request.region)
    fee = base_fee(zone) + weight_surcharge(grams)
    if request.method == "express":
        fee = q2(fee * config.get("shipping.express_multiplier"))
        reason = None
    else:
        fee, reason = _standard_fee(request, fee)
    return ShippingQuote(fee, zone, request.method, delivery_days(zone, request.method), reason, grams)


def shipping_options(request: ShippingRequest) -> dict[str, ShippingQuote]:
    """Quote every method the order can use, keyed by method name.

    A normal order gets both standard and express. A gift-card-only order gets standard only,
    because express is not offered there (SHP-05). Any other refusal, such as the weight limit,
    still raises.

        SP, 300 g, merchandise 120.00 -> {"standard": fee 10.00, "express": fee 15.00}
    """
    options: dict[str, ShippingQuote] = {}
    for method in METHODS:
        try:
            options[method] = quote_shipping(replace(request, method=method))
        except PolicyError as error:
            if error.reason != "express_not_available":
                raise
    return options


def estimated_delivery(quote: ShippingQuote, shipped_on: date) -> date | None:
    """Day the goods arrive when shipped on `shipped_on`, or None when nothing is delivered (SHP-04).

    A standard shipment to zone 1 shipped on March 10 arrives on March 13 (SHP-06).
    """
    if quote.estimated_days == 0:
        return None
    return shipped_on + timedelta(days=quote.estimated_days)


def describe_shipping(quote: ShippingQuote) -> str:
    """One line for receipts and support.

        standard 10.00 to zone 1 in 3 days
        standard 0.00 to zone 1 in 3 days (free: threshold)
        standard 0.00 (free: digital)
    """
    if quote.estimated_days == 0:
        return f"{quote.method} {quote.fee} (free: {quote.free_reason})"
    text = f"{quote.method} {quote.fee} to zone {quote.zone} in {quote.estimated_days} days"
    return f"{text} (free: {quote.free_reason})" if quote.free_reason else text

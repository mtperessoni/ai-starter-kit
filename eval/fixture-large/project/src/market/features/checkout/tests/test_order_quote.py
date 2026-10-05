"""Tests for order_quote (CHK-03, CHK-04, SHP-03, TAX-01, LOY-04)."""
from decimal import Decimal

import pytest

from market.features.cart.cart_service import get_cart
from market.features.checkout.order_quote import build_quote, delivery_region, explain_quote
from market.features.checkout.ports import set_loyalty_port
from market.features.checkout.tests.helpers import ADDR, cart_with
from market.features.inventory.stock_store import on_hand
from market.features.loyalty.points_ledger import add_points
from market.features.loyalty.points_redemption import LoyaltyRedemptionPort
from market.infra.customers import get_customer
from market.infra.errors import PolicyError, ValidationError
from market.infra.models import Address
from market.infra.repositories import repo


def quote(customer, items, address=ADDR, method="standard", points=0, coupons=()):
    cart_id = cart_with(customer, items, coupons)
    return build_quote(get_cart(cart_id), get_customer(customer), address, method, points)


class RecordingPort:
    def __init__(self, value="0.00"):
        self.value = Decimal(value)
        self.calls = []

    def redemption_value(self, customer_id, points, merchandise_total):
        self.calls.append((customer_id, points, merchandise_total))
        return self.value


def test_total_is_merchandise_plus_shipping_plus_tax():
    result = quote("C-REG", [("BK-100", 1)])
    assert (result.shipping.fee, result.tax.total, result.total) == (
        Decimal("10.00"), Decimal("0.80"), Decimal("50.80"))


def test_free_shipping_order_total():
    result = quote("C-REG", [("EL-200", 1), ("HM-100", 1)])
    assert (result.shipping.fee, result.tax.total, result.total) == (
        Decimal("0.00"), Decimal("16.00"), Decimal("216.00"))


def test_loyalty_discount_reduces_the_amount_to_pay_not_the_tax():
    set_loyalty_port(LoyaltyRedemptionPort())
    add_points("C-REG", 500, "grant")
    result = quote("C-REG", [("EL-200", 1), ("HM-100", 1)], points=500)
    assert (result.loyalty_discount, result.tax.total, result.total) == (
        Decimal("5.00"), Decimal("16.00"), Decimal("211.00"))
    assert result.points_to_redeem == 500


def test_points_above_the_balance_are_refused():
    set_loyalty_port(LoyaltyRedemptionPort())
    with pytest.raises(PolicyError):
        quote("C-REG", [("EL-200", 1)], points=500)


def test_without_a_port_points_are_refused():
    with pytest.raises(PolicyError) as error:
        quote("C-REG", [("EL-200", 1)], points=500)
    assert error.value.reason == "loyalty_unavailable"


def test_negative_points_are_invalid():
    with pytest.raises(ValidationError):
        quote("C-REG", [("EL-200", 1)], points=-100)


def test_total_never_goes_below_zero():
    set_loyalty_port(RecordingPort("1000.00"))
    assert quote("C-REG", [("BK-100", 1)]).total == Decimal("0.00")


def test_the_port_sees_merchandise_after_discounts():
    port = RecordingPort()
    set_loyalty_port(port)
    quote("C-REG", [("EL-200", 1)], coupons=("SAVE20",))
    assert port.calls == [("C-REG", 0, Decimal("96.00"))]


def test_without_an_address_the_customer_region_is_used():
    result = quote("C-RJ", [("HM-100", 1)], address=None)
    assert (result.shipping.fee, result.tax.total, result.total) == (
        Decimal("21.00"), Decimal("10.10"), Decimal("111.10"))


def test_the_address_region_wins_over_the_customer_region():
    result = quote("C-REG", [("BK-100", 1)], address=Address("BR", "AM", "69000-000"))
    assert (result.shipping.zone, result.tax.rate, result.total) == (3, Decimal("7"), Decimal("72.10"))


def test_express_costs_more_and_is_taxed():
    result = quote("C-REG", [("BK-100", 1)], method="express")
    assert (result.shipping.fee, result.total) == (Decimal("15.00"), Decimal("56.20"))


def test_a_free_shipping_coupon_waives_standard():
    result = quote("C-REG", [("BK-100", 1)], coupons=("FREESHIP",))
    assert (result.shipping.free_reason, result.total) == ("coupon", Decimal("40.00"))


def test_quoting_changes_nothing():
    cart_id = cart_with("C-REG", [("EL-200", 1)])
    build_quote(get_cart(cart_id), get_customer("C-REG"), ADDR, "standard", 0)
    assert on_hand("EL-200") == 5 and repo("orders").all() == [] and get_cart(cart_id).status == "open"


def test_delivery_region_prefers_the_address():
    assert delivery_region(None, get_customer("C-RJ")) == "RJ"
    assert delivery_region(ADDR, get_customer("C-RJ")) == "SP"


def test_explain_quote_lists_each_money_component():
    set_loyalty_port(LoyaltyRedemptionPort())
    add_points("C-REG", 500, "grant")
    result = quote("C-REG", [("EL-200", 1), ("HM-100", 1)], points=500)
    assert explain_quote(result) == [
        "merchandise 200.00", "shipping 0.00 (threshold)", "tax 16.00", "loyalty -5.00", "total 211.00"]


def test_explain_quote_skips_loyalty_when_unused():
    assert explain_quote(quote("C-REG", [("BK-100", 1)])) == [
        "merchandise 40.00", "shipping 10.00", "tax 0.80", "total 50.80"]

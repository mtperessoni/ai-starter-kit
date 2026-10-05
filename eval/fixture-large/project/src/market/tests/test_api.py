"""Smoke tests of market.api with the demo data (CHK-02, CHK-09, PAY-05, LOY-01, RET-07, NTF-01, INV-08)."""
from datetime import date, datetime
from decimal import Decimal

import pytest

import market
from market import api

ADDR = api.Address("BR", "SP", "01000-000")
OK = api.PaymentRequest("card", "ok_1")
DECLINE = api.PaymentRequest("card", "decline_1")


@pytest.fixture(autouse=True)
def demo():
    api.seed_demo()


def cart_with(customer, *items, coupon=None):
    cart = api.create_cart(customer)
    for sku, qty in items:
        api.add_to_cart(cart, sku, qty)
    if coupon:
        api.apply_coupon(cart, coupon)
    return cart


def test_the_package_exposes_the_api_and_a_version():
    assert market.api is api and market.__version__ == "0.1.0"


def test_seed_demo_loads_the_demo_data():
    assert api.get_product("EL-200").price == Decimal("120.00")
    assert api.available_stock("EL-200") == 5 and api.available_stock("GC-050") > 10**6
    assert api.gift_card_balance("GIFT-100") == Decimal("100.00")
    assert len(api.search_products()) == 9 and api.get_config("shipping.free_threshold") == Decimal("200.00")


def test_seed_demo_twice_starts_from_a_clean_state():
    cart_with("C-REG", ("EL-200", 1))
    api.seed_demo()
    assert api.available_stock("EL-200") == 5 and api.event_history() == []


def test_a_quote_lists_discounts_and_totals():
    cart = cart_with("C-REG", ("EL-200", 1), coupon="SAVE20")
    quote = api.quote_cart(cart)
    assert (quote.discount_total, quote.total) == (Decimal("24.00"), Decimal("96.00"))
    order_quote = api.quote_order(cart, ADDR)
    assert order_quote.total == Decimal("114.48")


def test_a_paid_order_earns_points_and_sends_the_confirmation():
    order = api.place_order(cart_with("C-REG", ("EL-200", 1)), OK, ADDR)
    assert order.status == "paid" and api.points_balance("C-REG") == 120
    sent = api.sent_notifications("reg@example.com", "order_confirmation")
    assert [n.order_id for n in sent] == [order.order_id]
    assert api.get_payment(order.payment_id).status == "captured"


def test_a_declined_payment_returns_the_order_and_sends_payment_failed():
    order = api.place_order(cart_with("C-REG", ("BK-100", 2)), DECLINE, ADDR)
    assert order.status == "payment_failed" and order.decline_code == "card_declined"
    assert api.available_stock("BK-100") == 100
    assert len(api.sent_notifications("reg@example.com", "payment_failed")) == 1


def test_redeeming_points_lowers_the_amount_to_pay():
    api.grant_points("C-REG", 500)
    cart = cart_with("C-REG", ("EL-200", 1), ("HM-100", 1))
    order = api.place_order(cart, OK, ADDR, points_to_redeem=500)
    assert order.loyalty_discount == Decimal("5.00") and order.total == Decimal("211.00")
    assert api.points_balance("C-REG") == 200


def test_cancel_reverses_stock_points_and_notifies():
    order = api.place_order(cart_with("C-REG", ("EL-200", 1)), OK, ADDR)
    api.cancel_order(order.order_id)
    assert api.available_stock("EL-200") == 5 and api.points_balance("C-REG") == 0
    assert len(api.sent_notifications(template="order_cancelled")) == 1


def test_a_delivered_order_can_be_returned():
    order = api.place_order(cart_with("C-REG", ("BK-100", 1)), OK, ADDR)
    api.mark_shipped(order.order_id)
    api.mark_delivered(order.order_id)
    api.advance_time(days=10)
    result = api.request_return(order.order_id, [("BK-100", 1)], "changed_mind")
    assert result.status == "completed" and api.get_return(result.return_id) == result
    assert api.get_order(order.order_id).status == "refunded"
    assert api.points_balance("C-REG") == 0


def test_a_gift_card_pays_an_order():
    cart = cart_with("C-REG", ("BK-100", 1))
    order = api.place_order(cart, api.PaymentRequest("gift_card", gift_card_code="GIFT-100"), ADDR)
    assert order.status == "paid" and api.gift_card_balance("GIFT-100") == Decimal("49.20")


def test_low_stock_reaches_ops():
    api.set_stock("EL-200", 7)
    api.place_order(cart_with("C-REG", ("EL-200", 3)), OK, ADDR)
    assert api.available_stock("EL-200") == 4
    assert len(api.sent_notifications("ops@market.test", "low_stock")) == 1


def test_errors_are_the_market_error_of_the_rule():
    cart = api.create_cart("C-REG")
    with pytest.raises(api.OutOfStockError):
        api.add_to_cart(cart, "EL-200", 6)
    with pytest.raises(api.ValidationError):
        api.place_order(cart_with("C-REG", ("EL-200", 1)), OK, None)
    with pytest.raises(api.NotFoundError):
        api.get_order("ORD-9999")
    with pytest.raises(api.PolicyError):
        api.cancel_order(api.place_order(cart_with("C-REG", ("BK-100", 1)), DECLINE, ADDR).order_id)
    assert issubclass(api.PolicyError, api.MarketError)


def test_config_and_clock_are_reachable():
    api.set_config("checkout.min_order_total", Decimal("100.00"))
    with pytest.raises(api.ValidationError):
        api.place_order(cart_with("C-REG", ("BK-100", 1)), OK, ADDR)
    assert api.advance_time(days=1).date() == date(2026, 3, 11)
    api.set_now(datetime(2026, 4, 1, 9, 0))
    assert api.get_config("checkout.min_order_total") == Decimal("100.00")

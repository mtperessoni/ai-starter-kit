"""Tests for loyalty_events (LOY-01, LOY-03, LOY-06): handlers fed through the event bus."""
from decimal import Decimal

import pytest

import market.features.loyalty  # noqa: F401  (registers the handlers)
from market.features.loyalty.loyalty_events import handled_events, register
from market.features.loyalty.points_ledger import add_points, balance
from market.infra import events
from market.infra.customers import add_customer
from market.infra.models import Customer


@pytest.fixture(autouse=True)
def customers():
    add_customer(Customer("C-REG", "reg@example.com"))
    add_customer(Customer("C-VIP", "vip@example.com", "vip"))


def paid(customer="C-REG", base="120.00", redeemed=0, order="ORD-0001"):
    events.publish("order.paid", order_id=order, customer_id=customer, points_base=Decimal(base),
                   points_redeemed=redeemed, total=Decimal(base))


def test_a_paid_order_earns_points():
    paid()
    assert balance("C-REG") == 120


def test_vip_earns_double():
    paid("C-VIP")
    assert balance("C-VIP") == 240


def test_gift_card_only_orders_earn_nothing():
    paid(base="0.00")
    assert balance("C-REG") == 0


def test_registering_twice_does_not_earn_twice():
    register()
    register()
    paid()
    assert balance("C-REG") == 120


def test_redeemed_points_are_spent_on_payment():
    add_points("C-REG", 500, "grant")
    paid(redeemed=500)
    assert balance("C-REG") == 120


def test_a_cancelled_order_takes_back_earned_points_and_returns_redeemed_ones():
    add_points("C-REG", 500, "grant")
    paid(redeemed=500)
    events.publish("order.cancelled", order_id="ORD-0001", customer_id="C-REG",
                   points_base=Decimal("120.00"), points_redeemed=500)
    assert balance("C-REG") == 500


def test_claw_back_never_goes_below_zero():
    events.publish("order.cancelled", order_id="ORD-0001", customer_id="C-REG",
                   points_base=Decimal("120.00"), points_redeemed=0)
    assert balance("C-REG") == 0


def test_a_completed_return_takes_back_the_points_of_the_returned_goods():
    paid()
    events.publish("return.completed", return_id="RET-0001", order_id="ORD-0001", customer_id="C-REG",
                   points_base_returned=Decimal("40.00"), refund_total=Decimal("43.20"))
    assert balance("C-REG") == 80


def test_handled_events_match_the_registered_subscriptions():
    assert handled_events() == ("order.paid", "order.cancelled", "return.completed")

"""Tests for notification_events (NTF-01 to NTF-05): handlers fed through the event bus."""
from decimal import Decimal

import pytest

import market.features.notifications  # noqa: F401  (registers the handlers)
from market.features.notifications.dispatcher import list_sent
from market.features.notifications.notification_events import handled_events
from market.infra import events
from market.infra.customers import add_customer
from market.infra.models import Customer


@pytest.fixture(autouse=True)
def customers():
    add_customer(Customer("C-REG", "reg@example.com"))


def test_a_paid_order_sends_the_confirmation():
    events.publish("order.paid", order_id="ORD-0001", customer_id="C-REG", points_base=Decimal("10.00"),
                   points_redeemed=0, total=Decimal("10.00"))
    sent = list_sent("reg@example.com", "order_confirmation")
    assert [n.order_id for n in sent] == ["ORD-0001"]


def test_a_failed_payment_sends_payment_failed():
    events.publish("payment.failed", payment_id="PAY-0001", order_id="ORD-0001", customer_id="C-REG",
                   code="card_declined")
    assert len(list_sent("reg@example.com", "payment_failed")) == 1


def test_a_cancelled_order_sends_order_cancelled():
    events.publish("order.cancelled", order_id="ORD-0001", customer_id="C-REG",
                   points_base=Decimal("10.00"), points_redeemed=0)
    assert list_sent("reg@example.com", "order_cancelled")[0].subject == "Order ORD-0001 cancelled"


def test_a_completed_return_sends_return_completed():
    events.publish("return.completed", return_id="RET-0001", order_id="ORD-0001", customer_id="C-REG",
                   points_base_returned=Decimal("10.00"), refund_total=Decimal("10.00"))
    assert list_sent("reg@example.com", "return_completed")[0].subject == "Return RET-0001 completed"


def test_low_stock_goes_to_ops():
    events.publish("inventory.low_stock", sku="EL-200", available=4)
    sent = list_sent("ops@market.test", "low_stock")
    assert [n.subject for n in sent] == ["Low stock: EL-200 has 4 left"]


def test_an_event_repeated_for_the_same_order_sends_once():
    for _ in range(2):
        events.publish("payment.failed", payment_id="PAY-0001", order_id="ORD-0001",
                       customer_id="C-REG", code="card_declined")
    assert len(list_sent(template="payment_failed")) == 1


def test_handled_events_lists_every_subscription():
    assert handled_events() == ("order.paid", "payment.failed", "order.cancelled", "return.completed",
                                "inventory.low_stock")

"""Tests for dispatcher (NTF-05): sending once and listing."""
import pytest

from market.features.notifications.dispatcher import count_sent, last_sent, list_sent, preview, recipients, send
from market.infra import clock
from market.infra.errors import ValidationError


def test_send_records_a_notification():
    sent = send("order_confirmation", "reg@example.com", "ORD-0001")
    assert sent is not None and sent.notification_id == "NTF-0001"
    assert sent.subject == "Order ORD-0001 confirmed" and sent.sent_at == clock.now()


def test_the_same_template_order_and_recipient_goes_out_once():
    assert send("order_confirmation", "reg@example.com", "ORD-0001") is not None
    assert send("order_confirmation", "reg@example.com", "ORD-0001") is None
    assert len(list_sent()) == 1


def test_another_recipient_order_or_template_is_sent():
    send("order_confirmation", "reg@example.com", "ORD-0001")
    assert send("order_confirmation", "vip@example.com", "ORD-0001") is not None
    assert send("order_confirmation", "reg@example.com", "ORD-0002") is not None
    assert send("order_cancelled", "reg@example.com", "ORD-0001") is not None


def test_notifications_without_an_order_are_never_suppressed():
    send("low_stock", "ops@market.test", None, sku="EL-200", available=3)
    assert send("low_stock", "ops@market.test", None, sku="EL-200", available=2) is not None


def test_list_sent_filters_by_recipient_and_template():
    send("order_confirmation", "reg@example.com", "ORD-0001")
    send("order_cancelled", "reg@example.com", "ORD-0001")
    send("order_confirmation", "vip@example.com", "ORD-0002")
    assert len(list_sent()) == 3
    assert len(list_sent("reg@example.com")) == 2
    assert [n.recipient for n in list_sent(template="order_confirmation")] == ["reg@example.com", "vip@example.com"]


def test_a_recipient_must_be_an_email():
    with pytest.raises(ValidationError):
        send("order_confirmation", "nobody", "ORD-0001")


def test_count_sent_and_last_sent():
    send("order_confirmation", "reg@example.com", "ORD-0001")
    send("order_cancelled", "reg@example.com", "ORD-0001")
    assert count_sent() == 2 and count_sent("reg@example.com", "order_cancelled") == 1
    assert last_sent("reg@example.com").template == "order_cancelled"
    assert last_sent("reg@example.com", "order_confirmation").order_id == "ORD-0001"
    assert last_sent("nobody@example.com") is None


def test_preview_renders_without_recording():
    assert preview("order_cancelled", order_id="ORD-0007") == "Order ORD-0007 cancelled"
    assert list_sent() == []


def test_recipients_are_distinct_and_in_first_seen_order():
    send("order_confirmation", "reg@example.com", "ORD-0001")
    send("order_confirmation", "vip@example.com", "ORD-0002")
    send("order_cancelled", "reg@example.com", "ORD-0001")
    assert recipients() == ["reg@example.com", "vip@example.com"]

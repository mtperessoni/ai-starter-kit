"""Tests for payment_service (PAY-01 to PAY-08): charge, retries, idempotency and refunds."""
from decimal import Decimal

import pytest

from market.features.payments.gift_cards import gift_card_balance, issue_gift_card
from market.features.payments.payment_models import PaymentRequest
from market.features.payments.payment_service import (charge, describe, get_payment, payments_for_order, refund,
                                                      total_refunded)
from market.infra import config, events
from market.infra.customers import add_customer
from market.infra.errors import NotFoundError, PolicyError, ValidationError
from market.infra.models import Customer
from market.infra.repositories import repo

HUNDRED = Decimal("100.00")


@pytest.fixture(autouse=True)
def customer():
    add_customer(Customer("C-1", "one@example.com"))


def pay(request, amount=HUNDRED, order="ORD-0001"):
    return charge(order, "C-1", amount, request)


def test_card_payment_is_captured():
    payment = pay(PaymentRequest("card", "ok_1"))
    assert payment.status == "captured" and payment.captured == HUNDRED
    assert payment.gateway_ref == "GW-ok_1" and payment.decline_code is None
    assert payment.payment_id == "PAY-0001"


def test_pix_payment_is_captured():
    assert pay(PaymentRequest("pix", "ok_pix")).status == "captured"


def test_unknown_method_is_rejected():
    with pytest.raises(ValidationError):
        pay(PaymentRequest("cheque", "ok_1"))


def test_pix_is_one_installment_only():
    with pytest.raises(ValidationError):
        pay(PaymentRequest("pix", "ok_1", installments=2))


def test_card_installments_are_limited_to_six():
    with pytest.raises(ValidationError):
        pay(PaymentRequest("card", "ok_1", installments=7))


def test_each_installment_must_reach_the_minimum():
    with pytest.raises(ValidationError):
        pay(PaymentRequest("card", "ok_1", installments=2), Decimal("15.00"))


def test_interest_is_captured_but_not_part_of_the_amount():
    payment = pay(PaymentRequest("card", "ok_1", installments=3))
    assert payment.amount == HUNDRED and payment.captured == Decimal("103.98")
    assert payment.installment_amount == Decimal("34.66")


def test_decline_is_recorded_and_never_captured():
    payment = pay(PaymentRequest("card", "decline_1"))
    assert payment.status == "failed" and payment.decline_code == "card_declined"
    assert payment.captured == Decimal("0.00")


def test_decline_raises_a_payment_failed_event():
    payment = pay(PaymentRequest("card", "fraud_1"))
    event = events.history("payment.failed")[0]
    assert event.payload == {"payment_id": payment.payment_id, "order_id": "ORD-0001",
                             "customer_id": "C-1", "code": "suspected_fraud"}
    assert events.history("payment.captured") == []


def test_capture_raises_a_captured_event():
    payment = pay(PaymentRequest("card", "ok_1"))
    assert events.history("payment.captured")[0].payload["payment_id"] == payment.payment_id


def test_a_timeout_is_retried_until_it_approves():
    payment = pay(PaymentRequest("card", "flaky_2"))
    assert payment.status == "captured" and payment.gateway_ref == "GW-flaky_2"


def test_three_timeouts_decline_as_gateway_timeout():
    payment = pay(PaymentRequest("card", "flaky_3"))
    assert payment.status == "failed" and payment.decline_code == "gateway_timeout"
    assert pay(PaymentRequest("card", "timeout_always"), order="ORD-0002").decline_code == "gateway_timeout"


def test_attempts_follow_config():
    config.set("payments.max_attempts", 1)
    assert pay(PaymentRequest("card", "flaky_1")).decline_code == "gateway_timeout"


def test_gift_card_payment_takes_the_balance():
    issue_gift_card("GIFT-100", Decimal("100.00"))
    payment = pay(PaymentRequest("gift_card", gift_card_code="GIFT-100"), Decimal("60.00"))
    assert payment.status == "captured" and gift_card_balance("GIFT-100") == Decimal("40.00")


def test_gift_card_without_enough_balance_is_declined():
    issue_gift_card("GIFT-100", Decimal("10.00"))
    payment = pay(PaymentRequest("gift_card", gift_card_code="GIFT-100"), Decimal("60.00"))
    assert payment.decline_code == "insufficient_balance" and gift_card_balance("GIFT-100") == Decimal("10.00")


def test_unknown_gift_card_is_declined():
    assert pay(PaymentRequest("gift_card", gift_card_code="NOPE")).decline_code == "unknown_gift_card"
    assert pay(PaymentRequest("gift_card"), order="ORD-0002").decline_code == "unknown_gift_card"


def test_same_idempotency_key_returns_the_first_payment():
    first = pay(PaymentRequest("card", "ok_1", idempotency_key="K1"))
    second = pay(PaymentRequest("card", "ok_1", idempotency_key="K1"), order="ORD-0002")
    assert second is first and len(repo("payments").all()) == 1


def test_a_different_key_charges_again():
    pay(PaymentRequest("card", "ok_1", idempotency_key="K1"))
    pay(PaymentRequest("card", "ok_1", idempotency_key="K2"), order="ORD-0002")
    assert len(repo("payments").all()) == 2


def test_partial_refund_keeps_the_payment_open():
    payment = pay(PaymentRequest("card", "ok_1"))
    refund(payment.payment_id, Decimal("40.00"))
    assert payment.status == "partially_refunded" and payment.refunded == Decimal("40.00")


def test_full_refund_closes_the_payment():
    payment = pay(PaymentRequest("card", "ok_1"))
    refund(payment.payment_id, Decimal("60.00"))
    refund(payment.payment_id, Decimal("40.00"))
    assert payment.status == "refunded"
    assert [e.payload["amount"] for e in events.history("payment.refunded")] == [Decimal("60.00"), Decimal("40.00")]


def test_refunds_never_exceed_what_was_paid():
    payment = pay(PaymentRequest("card", "ok_1"))
    refund(payment.payment_id, Decimal("70.00"))
    with pytest.raises(PolicyError) as error:
        refund(payment.payment_id, Decimal("30.01"))
    assert error.value.reason == "refund_exceeds_captured"


def test_interest_is_not_refunded():
    payment = pay(PaymentRequest("card", "ok_1", installments=3))
    with pytest.raises(PolicyError):
        refund(payment.payment_id, Decimal("103.98"))
    refund(payment.payment_id, HUNDRED)
    assert payment.status == "refunded"


def test_gift_card_refund_goes_back_to_the_balance():
    issue_gift_card("GIFT-100", Decimal("100.00"))
    payment = pay(PaymentRequest("gift_card", gift_card_code="GIFT-100"), Decimal("60.00"))
    refund(payment.payment_id, Decimal("25.00"))
    assert gift_card_balance("GIFT-100") == Decimal("65.00")


def test_a_failed_payment_cannot_be_refunded():
    payment = pay(PaymentRequest("card", "decline_1"))
    with pytest.raises(PolicyError):
        refund(payment.payment_id, Decimal("1.00"))


def test_refund_amount_must_be_positive():
    payment = pay(PaymentRequest("card", "ok_1"))
    with pytest.raises(ValidationError):
        refund(payment.payment_id, Decimal("0.00"))


def test_unknown_payment_is_not_found():
    with pytest.raises(NotFoundError):
        get_payment("PAY-9999")


def test_payments_of_an_order_include_failed_attempts():
    pay(PaymentRequest("card", "decline_1"))
    pay(PaymentRequest("card", "ok_1"))
    pay(PaymentRequest("card", "ok_1"), order="ORD-0002")
    assert [p.status for p in payments_for_order("ORD-0001")] == ["failed", "captured"]


def test_total_refunded_sums_the_payments_of_an_order():
    first = pay(PaymentRequest("card", "ok_1"))
    refund(first.payment_id, Decimal("30.00"))
    refund(first.payment_id, Decimal("20.00"))
    assert total_refunded("ORD-0001") == Decimal("50.00") and total_refunded("ORD-0002") == Decimal("0.00")


def test_describe_summarizes_a_payment_in_one_line():
    assert describe(pay(PaymentRequest("card", "ok_1", installments=3))) == (
        "PAY-0001 card captured 100.00 in 3x of 34.66")
    assert describe(pay(PaymentRequest("card", "decline_1"), order="ORD-0002")) == (
        "PAY-0002 card failed 100.00 (card_declined)")
    assert describe(pay(PaymentRequest("pix", "ok_1"), order="ORD-0003")) == "PAY-0003 pix captured 100.00"

"""Tests for gateway (PAY-03, PAY-04): the fake gateway tokens."""
from decimal import Decimal

from market.features.payments.gateway import authorize, describe_token

AMOUNT = Decimal("50.00")


def test_ok_token_is_approved_with_a_reference():
    result = authorize("card", "ok_1", AMOUNT, 1)
    assert result.approved and result.reference == "GW-ok_1"


def test_decline_token_is_card_declined():
    result = authorize("card", "decline_1", AMOUNT, 1)
    assert not result.approved and result.code == "card_declined" and result.reference is None


def test_fraud_token_is_suspected_fraud():
    assert authorize("card", "fraud_9", AMOUNT, 1).code == "suspected_fraud"


def test_flaky_times_out_then_approves():
    codes = [authorize("card", "flaky_2", AMOUNT, attempt) for attempt in (1, 2, 3)]
    assert [c.code for c in codes] == ["gateway_timeout", "gateway_timeout", "approved"]
    assert codes[2].approved


def test_timeout_always_never_approves():
    assert all(authorize("card", "timeout_always", AMOUNT, n).code == "gateway_timeout" for n in (1, 5, 9))


def test_unknown_token_is_invalid():
    assert authorize("card", "whatever", AMOUNT, 1).code == "invalid_token"
    assert authorize("card", "flaky_x", AMOUNT, 1).code == "invalid_token"
    assert authorize("pix", "", AMOUNT, 1).code == "invalid_token"


def test_describe_token_explains_every_shape():
    assert describe_token("ok_1") == "approves"
    assert describe_token("decline_1") == "declines as card_declined"
    assert describe_token("fraud_1") == "declines as suspected_fraud"
    assert describe_token("timeout_always") == "always times out"
    assert describe_token("flaky_2") == "times out twice, then approves"
    assert describe_token("flaky_1") == "times out once, then approves"
    assert describe_token("flaky_5") == "times out 5 times, then approves"
    assert describe_token("nope") == "declines as invalid_token"

"""Tests for gift_cards (PAY-05, PAY-07): balances."""
from decimal import Decimal

import pytest

from market.features.payments.gift_cards import (credit_gift_card, debit_gift_card, gift_card_balance,
                                                 has_gift_card, issue_gift_card, outstanding_balance)
from market.infra.errors import NotFoundError, PolicyError, ValidationError


def test_issue_and_read_a_balance():
    issue_gift_card("GIFT-100", Decimal("100.00"))
    assert gift_card_balance("GIFT-100") == Decimal("100.00") and has_gift_card("GIFT-100")


def test_codes_are_normalized():
    issue_gift_card(" gift-1 ", Decimal("10.00"))
    assert gift_card_balance("GIFT-1") == Decimal("10.00")


def test_unknown_code_is_not_found():
    with pytest.raises(NotFoundError):
        gift_card_balance("NOPE")
    assert not has_gift_card("NOPE")


def test_a_code_is_issued_once():
    issue_gift_card("GIFT-1", Decimal("10.00"))
    with pytest.raises(ValidationError):
        issue_gift_card("GIFT-1", Decimal("5.00"))


def test_debit_takes_from_the_balance():
    issue_gift_card("GIFT-1", Decimal("100.00"))
    debit_gift_card("GIFT-1", Decimal("30.00"))
    assert gift_card_balance("GIFT-1") == Decimal("70.00")


def test_debit_above_the_balance_changes_nothing():
    issue_gift_card("GIFT-1", Decimal("100.00"))
    with pytest.raises(PolicyError) as error:
        debit_gift_card("GIFT-1", Decimal("100.01"))
    assert error.value.reason == "insufficient_balance"
    assert gift_card_balance("GIFT-1") == Decimal("100.00")


def test_credit_gives_money_back():
    issue_gift_card("GIFT-1", Decimal("10.00"))
    credit_gift_card("GIFT-1", Decimal("5.50"))
    assert gift_card_balance("GIFT-1") == Decimal("15.50")


def test_amounts_must_be_positive():
    issue_gift_card("GIFT-1", Decimal("10.00"))
    with pytest.raises(ValidationError):
        debit_gift_card("GIFT-1", Decimal("0.00"))
    with pytest.raises(ValidationError):
        credit_gift_card("GIFT-1", Decimal("-1.00"))


def test_outstanding_balance_sums_every_card():
    issue_gift_card("GIFT-1", Decimal("10.00"))
    issue_gift_card("GIFT-2", Decimal("5.50"))
    assert outstanding_balance() == Decimal("15.50")

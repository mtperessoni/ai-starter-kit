"""Tests for return_policy (RET-01, RET-02, RET-05): window, categories, quantities, reasons."""
from datetime import date, timedelta

import pytest

from market.features.returns.return_policy import (REASONS, check_eligibility, merge_items, return_deadline,
                                                      return_window_open, returnable_units)
from market.features.returns.tests.helpers import make_order, order_line
from market.infra import config
from market.infra.errors import PolicyError, ValidationError

DAY0 = date(2026, 3, 10)


def laptop_order(**kwargs):
    return make_order([order_line("EL-200", "electronics", 3, "360.00")], **kwargs)


def test_a_delivered_order_can_be_returned():
    check_eligibility(laptop_order(), [("EL-200", 1)], "changed_mind", DAY0)


def test_a_partially_refunded_order_can_be_returned_again():
    check_eligibility(laptop_order(status="partially_refunded", returned={"EL-200": 1}),
                      [("EL-200", 2)], "other", DAY0)


def test_the_window_is_30_days_after_delivery():
    check_eligibility(laptop_order(), [("EL-200", 1)], "other", DAY0 + timedelta(days=30))
    with pytest.raises(PolicyError) as error:
        check_eligibility(laptop_order(), [("EL-200", 1)], "other", DAY0 + timedelta(days=31))
    assert error.value.reason == "return_window_closed"


def test_the_window_follows_config():
    config.set("returns.window_days", 10)
    with pytest.raises(PolicyError):
        check_eligibility(laptop_order(), [("EL-200", 1)], "other", DAY0 + timedelta(days=11))


def test_an_order_that_was_not_delivered_is_refused():
    with pytest.raises(PolicyError):
        check_eligibility(laptop_order(status="paid"), [("EL-200", 1)], "other", DAY0)


def test_gift_cards_cannot_be_returned():
    order = make_order([order_line("GC-050", "gift_card", 1, "50.00")])
    with pytest.raises(PolicyError) as error:
        check_eligibility(order, [("GC-050", 1)], "other", DAY0)
    assert error.value.reason == "not_returnable"


def test_grocery_cannot_be_returned():
    order = make_order([order_line("GR-100", "grocery", 2, "25.00")])
    with pytest.raises(PolicyError):
        check_eligibility(order, [("GR-100", 1)], "defective", DAY0)


def test_more_units_than_bought_minus_returned_are_refused():
    order = laptop_order(status="partially_refunded", returned={"EL-200": 2})
    with pytest.raises(ValidationError):
        check_eligibility(order, [("EL-200", 2)], "other", DAY0)


def test_repeated_skus_are_summed_before_the_check():
    with pytest.raises(ValidationError):
        check_eligibility(laptop_order(), [("EL-200", 2), ("EL-200", 2)], "other", DAY0)


def test_a_sku_not_in_the_order_is_refused():
    with pytest.raises(ValidationError):
        check_eligibility(laptop_order(), [("BK-100", 1)], "other", DAY0)


def test_the_four_reasons_are_accepted_and_others_are_not():
    for reason in REASONS:
        check_eligibility(laptop_order(), [("EL-200", 1)], reason, DAY0)
    with pytest.raises(ValidationError):
        check_eligibility(laptop_order(), [("EL-200", 1)], "bored", DAY0)


def test_an_empty_return_or_a_zero_quantity_is_invalid():
    with pytest.raises(ValidationError):
        check_eligibility(laptop_order(), [], "other", DAY0)
    with pytest.raises(ValidationError):
        merge_items([("EL-200", 0)])


def test_return_deadline_is_30_days_after_delivery():
    assert return_deadline(laptop_order()) == DAY0 + timedelta(days=30)
    assert return_deadline(laptop_order(status="paid")) is None


def test_returnable_units_leave_out_returned_units_and_unreturnable_categories():
    order = make_order([order_line("EL-200", "electronics", 3, "360.00"),
                        order_line("GC-050", "gift_card", 1, "50.00"),
                        order_line("BK-100", "books", 1, "40.00")],
                       status="partially_refunded", returned={"EL-200": 1, "BK-100": 1})
    assert returnable_units(order) == {"EL-200": 2}


def test_return_window_open_follows_the_deadline():
    order = laptop_order()
    assert return_window_open(order, DAY0 + timedelta(days=30)) is True
    assert return_window_open(order, DAY0 + timedelta(days=31)) is False
    assert return_window_open(laptop_order(status="paid"), DAY0) is False

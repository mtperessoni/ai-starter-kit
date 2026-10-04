"""Tests for return_service (RET-05, RET-06, RET-07): the whole return flow."""
from decimal import Decimal

import pytest

from market.features.cart.cart_service import add_item, create_cart
from market.features.checkout.order_lifecycle import get_order, mark_delivered, mark_shipped
from market.features.checkout.order_placement import place_order
from market.features.checkout.ports import set_loyalty_port
from market.features.inventory.stock_store import on_hand
from market.features.loyalty.points_ledger import add_points
from market.features.loyalty.points_redemption import LoyaltyRedemptionPort
from market.features.payments.payment_service import get_payment
from market.features.returns.return_service import (get_return, list_returns, refund_summary, request_return,
                                                      total_returned_value)
from market.features.returns.tests.helpers import ADDR, OK, delivered_order
from market.infra import clock, events
from market.infra.errors import NotFoundError, PolicyError, ValidationError


def test_a_return_refunds_merchandise_and_tax_of_the_units():
    order = delivered_order([("EL-200", 2)])
    result = request_return(order.order_id, [("EL-200", 1)], "changed_mind")
    assert (result.refund.merchandise, result.refund.tax, result.refund.total) == (
        Decimal("120.00"), Decimal("9.60"), Decimal("129.60"))
    assert result.status == "completed" and result.return_id == "RET-0001" and result.items == (("EL-200", 1),)
    payment = get_payment(order.payment_id)
    assert payment.refunded == Decimal("129.60") and payment.status == "partially_refunded"


def test_the_order_status_is_lowered():
    order = delivered_order([("EL-200", 2)])
    request_return(order.order_id, [("EL-200", 1)], "other")
    assert get_order(order.order_id).status == "partially_refunded"
    request_return(order.order_id, [("EL-200", 1)], "other")
    assert get_order(order.order_id).status == "refunded"
    assert get_payment(order.payment_id).status == "refunded"


def test_returned_goods_go_back_to_stock():
    order = delivered_order([("EL-200", 2)])
    assert on_hand("EL-200") == 3
    request_return(order.order_id, [("EL-200", 1)], "changed_mind")
    assert on_hand("EL-200") == 4


def test_defective_goods_do_not_go_back_to_stock():
    order = delivered_order([("EL-200", 2)])
    request_return(order.order_id, [("EL-200", 1)], "defective")
    assert on_hand("EL-200") == 3


def test_shipping_is_refunded_when_defective_goods_complete_the_order():
    order = delivered_order([("BK-100", 1)])
    result = request_return(order.order_id, [("BK-100", 1)], "defective")
    assert (result.refund.shipping, result.refund.total) == (Decimal("10.00"), Decimal("50.00"))
    assert get_order(order.order_id).status == "refunded"


def test_the_event_carries_points_base_and_refund_total():
    order = delivered_order([("EL-200", 2)])
    result = request_return(order.order_id, [("EL-200", 1)], "other")
    payload = events.history("return.completed")[0].payload
    assert payload["points_base_returned"] == Decimal("120.00") and payload["refund_total"] == Decimal("129.60")
    assert payload["return_id"] == result.return_id and payload["customer_id"] == "C-REG"


def test_books_carry_points_base_too():
    order = delivered_order([("BK-100", 1)])
    request_return(order.order_id, [("BK-100", 1)], "changed_mind")
    assert events.history("return.completed")[0].payload["points_base_returned"] == Decimal("40.00")


def test_more_units_than_bought_are_refused_and_nothing_is_refunded():
    order = delivered_order([("EL-200", 3)])
    request_return(order.order_id, [("EL-200", 2)], "other")
    with pytest.raises(ValidationError):
        request_return(order.order_id, [("EL-200", 2)], "other")
    assert len(events.history("return.completed")) == 1


def test_an_order_that_was_not_delivered_is_refused():
    cart = create_cart("C-REG")
    add_item(cart.cart_id, "EL-200", 1)
    order = place_order(cart.cart_id, OK, ADDR)
    with pytest.raises(PolicyError):
        request_return(order.order_id, [("EL-200", 1)], "other")


def test_the_30_day_window_is_enforced():
    order = delivered_order([("EL-200", 1)])
    clock.advance(days=31)
    with pytest.raises(PolicyError) as error:
        request_return(order.order_id, [("EL-200", 1)], "other")
    assert error.value.reason == "return_window_closed"


def test_gift_cards_cannot_be_returned():
    order = delivered_order([("GC-050", 1)])
    with pytest.raises(PolicyError):
        request_return(order.order_id, [("GC-050", 1)], "other")


def test_the_refund_is_capped_to_what_the_payment_holds():
    set_loyalty_port(LoyaltyRedemptionPort())
    add_points("C-REG", 500, "grant")
    cart = create_cart("C-REG")
    add_item(cart.cart_id, "EL-200", 1)
    add_item(cart.cart_id, "HM-100", 1)
    order = place_order(cart.cart_id, OK, ADDR, points_to_redeem=500)
    mark_shipped(order.order_id)
    mark_delivered(order.order_id)
    result = request_return(order.order_id, [("EL-200", 1), ("HM-100", 1)], "defective")
    assert result.refund.total == Decimal("211.00")
    assert get_payment(order.payment_id).status == "refunded"


def test_get_return_reads_the_record():
    order = delivered_order([("EL-200", 2)])
    result = request_return(order.order_id, [("EL-200", 1)], "other")
    assert get_return(result.return_id) == result


def test_an_unknown_return_is_not_found():
    with pytest.raises(NotFoundError):
        get_return("RET-9999")


def test_list_returns_filters_by_order_and_sums_the_refunds():
    first = delivered_order([("EL-200", 2)])
    request_return(first.order_id, [("EL-200", 1)], "other")
    request_return(first.order_id, [("EL-200", 1)], "other")
    second = delivered_order([("BK-100", 1)])
    request_return(second.order_id, [("BK-100", 1)], "other")
    assert len(list_returns()) == 3 and len(list_returns(first.order_id)) == 2
    assert total_returned_value(first.order_id) == Decimal("259.20")


def test_refund_summary_is_one_line():
    order = delivered_order([("EL-200", 2)])
    result = request_return(order.order_id, [("EL-200", 1)], "other")
    assert refund_summary(result) == "RET-0001 129.60 (merchandise 120.00, tax 9.60, shipping 0.00)"

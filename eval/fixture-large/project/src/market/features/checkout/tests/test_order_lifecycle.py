"""Tests for order_lifecycle (CHK-08, CHK-09, PRM-04, INV-05): moves, cancel, applied returns."""
import pytest

from market.features.checkout.order_lifecycle import (apply_return, awaiting_shipment, can_cancel, can_return,
                                                      cancel_order, days_since, get_order, list_orders, mark_delivered,
                                                      mark_shipped)
from market.features.checkout.order_placement import place_order
from market.features.checkout.tests.helpers import ADDR, DECLINE, OK, cart_with
from market.features.inventory.stock_store import available, on_hand
from market.features.payments.payment_service import get_payment
from market.features.promotions.promotion_usage import usage_count
from market.infra import clock, events
from market.infra.errors import NotFoundError, PolicyError, ValidationError


def paid(items=(("EL-200", 2),), coupons=(), customer="C-REG"):
    return place_order(cart_with(customer, list(items), coupons), OK, ADDR)


def delivered(items=(("EL-200", 2),)):
    order = paid(items)
    mark_shipped(order.order_id)
    return mark_delivered(order.order_id)


def test_a_paid_order_ships_then_is_delivered():
    order = paid()
    mark_shipped(order.order_id)
    assert order.status == "shipped" and order.shipped_at == clock.now()
    mark_delivered(order.order_id)
    assert order.status == "delivered" and order.delivered_at == clock.now()


def test_a_failed_order_cannot_ship():
    order = place_order(cart_with("C-REG", [("BK-100", 2)]), DECLINE, ADDR)
    with pytest.raises(PolicyError):
        mark_shipped(order.order_id)


def test_an_order_not_shipped_cannot_be_delivered():
    order = paid()
    with pytest.raises(PolicyError):
        mark_delivered(order.order_id)


def test_get_order_of_an_unknown_id_is_not_found():
    with pytest.raises(NotFoundError):
        get_order("ORD-9999")


def test_cancel_refunds_what_was_captured():
    order = paid()
    cancel_order(order.order_id)
    payment = get_payment(order.payment_id)
    assert order.status == "cancelled" and payment.status == "refunded" and payment.refunded == payment.amount


def test_cancel_puts_the_stock_back():
    order = paid()
    assert on_hand("EL-200") == 3
    cancel_order(order.order_id)
    assert on_hand("EL-200") == 5 and available("EL-200") == 5


def test_cancel_gives_the_coupon_use_back():
    order = paid([("EL-200", 1)], ("SAVE20",))
    assert usage_count("SAVE20", "C-REG") == 1
    cancel_order(order.order_id)
    assert usage_count("SAVE20", "C-REG") == 0


def test_cancel_publishes_the_event_with_the_points_to_reverse():
    order = paid([("EL-200", 1)])
    cancel_order(order.order_id)
    payload = events.history("order.cancelled")[0].payload
    assert payload["order_id"] == order.order_id and str(payload["points_base"]) == "120.00"


def test_a_shipped_order_cannot_be_cancelled():
    order = paid()
    mark_shipped(order.order_id)
    with pytest.raises(PolicyError) as error:
        cancel_order(order.order_id)
    assert error.value.reason == "cannot_cancel_shipped"


def test_an_order_cannot_be_cancelled_twice():
    order = paid()
    cancel_order(order.order_id)
    with pytest.raises(PolicyError):
        cancel_order(order.order_id)


def test_cancelling_a_gift_card_order_restocks_nothing():
    order = paid([("GC-050", 1)])
    cancel_order(order.order_id)
    assert order.status == "cancelled" and get_payment(order.payment_id).status == "refunded"


def test_a_partial_return_is_partially_refunded():
    order = delivered()
    apply_return(order.order_id, [("EL-200", 1)])
    assert order.status == "partially_refunded" and order.returned_units == {"EL-200": 1}


def test_returning_every_unit_is_refunded():
    order = delivered()
    apply_return(order.order_id, [("EL-200", 1)])
    apply_return(order.order_id, [("EL-200", 1)])
    assert order.status == "refunded"


def test_a_return_cannot_exceed_the_units_bought():
    order = delivered()
    with pytest.raises(ValidationError):
        apply_return(order.order_id, [("EL-200", 3)])


def test_a_paid_order_cannot_take_a_return():
    order = paid()
    with pytest.raises(PolicyError):
        apply_return(order.order_id, [("EL-200", 1)])


def test_list_orders_filters_by_customer_and_status():
    paid(customer="C-REG")
    paid([("BK-100", 1)], customer="C-VIP")
    cancel_order(paid([("BK-100", 1)]).order_id)
    assert len(list_orders()) == 3 and len(list_orders("C-VIP")) == 1
    assert [o.status for o in list_orders("C-REG", "cancelled")] == ["cancelled"]


def test_can_cancel_only_while_paid():
    order = paid()
    assert can_cancel(order) is True
    mark_shipped(order.order_id)
    assert can_cancel(order) is False


def test_can_return_needs_a_delivered_order_with_units_left():
    order = delivered()
    assert can_return(order) is True
    apply_return(order.order_id, [("EL-200", 2)])
    assert can_return(order) is False and can_return(paid()) is False


def test_awaiting_shipment_lists_paid_orders_oldest_first():
    first = paid([("BK-100", 1)])
    clock.advance(hours=1)
    second = paid([("BK-100", 1)])
    clock.advance(hours=1)
    third = paid([("BK-100", 1)])
    mark_shipped(second.order_id)
    assert [o.order_id for o in awaiting_shipment()] == [first.order_id, third.order_id]


def test_days_since_counts_whole_days_from_placement():
    order = paid()
    clock.advance(days=3, hours=5)
    assert days_since(order, clock.today()) == 3

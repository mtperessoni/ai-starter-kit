"""Tests for order_placement (CHK-01, CHK-02, CHK-06, PRM-04, INV-03, PRC-01)."""
from decimal import Decimal

import pytest

from market.features.cart.cart_service import get_cart
from market.features.catalog.product_store import deactivate_product, update_price
from market.features.checkout.order_placement import place_order
from market.features.checkout.ports import set_loyalty_port
from market.features.checkout.tests.helpers import ADDR, DECLINE, OK, cart_with
from market.features.inventory.reservations import get_reservation
from market.features.inventory.stock_store import available, on_hand, set_on_hand
from market.features.loyalty.points_ledger import add_points, balance
from market.features.loyalty.points_redemption import LoyaltyRedemptionPort
from market.features.payments.payment_models import PaymentRequest
from market.features.promotions.promotion_usage import usage_count
from market.infra import clock, events
from market.infra.errors import OutOfStockError, PolicyError, ValidationError
from market.infra.repositories import repo


def test_a_paid_order_keeps_the_quote_amounts():
    order = place_order(cart_with("C-REG", [("EL-200", 1)]), OK, ADDR)
    assert order.order_id == "ORD-0001" and order.status == "paid" and order.payment_id == "PAY-0001"
    assert (order.subtotal, order.shipping, order.tax, order.total) == (
        Decimal("120.00"), Decimal("10.00"), Decimal("10.40"), Decimal("140.40"))
    assert order.lines[0].tax == Decimal("9.60") and order.paid_at == clock.now()


def test_payment_commits_the_stock_and_converts_the_cart():
    cart_id = cart_with("C-REG", [("EL-200", 1)])
    order = place_order(cart_id, OK, ADDR)
    assert on_hand("EL-200") == 4 and available("EL-200") == 4
    assert get_reservation(order.reservation_id).status == "committed"
    assert get_cart(cart_id).status == "converted"


def test_a_coupon_use_counts_for_good_when_paid():
    order = place_order(cart_with("C-REG", [("EL-200", 1)], ("SAVE20",)), OK, ADDR)
    assert order.discount_total == Decimal("24.00") and order.total == Decimal("114.48")
    assert usage_count("SAVE20", "C-REG") == 1 and order.coupon_codes == ("SAVE20",)


def test_a_decline_returns_the_order_and_frees_the_stock():
    cart_id = cart_with("C-REG", [("BK-100", 2)])
    order = place_order(cart_id, DECLINE, ADDR)
    assert order.status == "payment_failed" and order.decline_code == "card_declined"
    assert available("BK-100") == 50 and get_reservation(order.reservation_id).status == "released"
    assert get_cart(cart_id).status == "open"


def test_a_retry_after_a_decline_is_a_new_order():
    cart_id = cart_with("C-REG", [("BK-100", 2)])
    first = place_order(cart_id, DECLINE, ADDR)
    second = place_order(cart_id, OK, ADDR)
    assert (first.order_id, second.order_id, second.status) == ("ORD-0001", "ORD-0002", "paid")


def test_order_paid_event_carries_the_points_base():
    order = place_order(cart_with("C-REG", [("EL-200", 1), ("GC-050", 1)]), OK, ADDR)
    payload = events.history("order.paid")[0].payload
    assert payload["order_id"] == order.order_id and payload["points_base"] == Decimal("120.00")
    assert payload["points_redeemed"] == 0 and payload["total"] == order.total


def test_a_decline_publishes_no_paid_event():
    place_order(cart_with("C-REG", [("BK-100", 2)]), DECLINE, ADDR)
    assert events.history("order.paid") == []


def test_an_empty_cart_is_refused():
    with pytest.raises(ValidationError):
        place_order(cart_with("C-REG", []), OK, ADDR)


def test_a_converted_cart_cannot_be_bought_again():
    cart_id = cart_with("C-REG", [("BK-100", 1)])
    place_order(cart_id, OK, ADDR)
    with pytest.raises(PolicyError) as error:
        place_order(cart_id, OK, ADDR)
    assert error.value.reason == "cart_not_open"


def test_an_expired_cart_cannot_be_bought():
    cart_id = cart_with("C-REG", [("BK-100", 1)])
    clock.advance(days=8)
    with pytest.raises(PolicyError) as error:
        place_order(cart_id, OK, ADDR)
    assert error.value.reason == "cart_expired"


def test_a_deactivated_product_cannot_be_bought():
    cart_id = cart_with("C-REG", [("BK-100", 1)])
    deactivate_product("BK-100")
    with pytest.raises(ValidationError):
        place_order(cart_id, OK, ADDR)


def test_short_stock_raises_and_holds_nothing():
    cart_id = cart_with("C-REG", [("EL-200", 2), ("BK-100", 1)])
    set_on_hand("EL-200", 1)
    with pytest.raises(OutOfStockError) as error:
        place_order(cart_id, OK, ADDR)
    assert error.value.skus == ("EL-200",)
    assert available("EL-200") == 1 and available("BK-100") == 50 and repo("orders").all() == []


def test_a_physical_order_without_address_holds_nothing():
    with pytest.raises(ValidationError):
        place_order(cart_with("C-REG", [("EL-200", 1)]), OK, None)
    assert available("EL-200") == 5 and repo("reservations").all() == []


def test_a_gift_card_order_needs_no_address_and_ships_nothing():
    order = place_order(cart_with("C-REG", [("GC-050", 1)]), OK, None)
    assert order.status == "paid" and order.shipping == Decimal("0.00") and order.total == Decimal("50.00")


def test_an_invalid_payment_request_releases_the_hold():
    with pytest.raises(ValidationError):
        place_order(cart_with("C-REG", [("EL-200", 1)]), PaymentRequest("cheque", "x"), ADDR)
    assert available("EL-200") == 5 and repo("orders").all() == []


def test_an_order_keeps_the_prices_it_was_placed_with():
    order = place_order(cart_with("C-REG", [("EL-200", 1)]), OK, ADDR)
    update_price("EL-200", Decimal("130.00"))
    assert repo("orders").get(order.order_id).lines[0].unit_price == Decimal("120.00")


def test_redeemed_points_reduce_the_amount_paid():
    set_loyalty_port(LoyaltyRedemptionPort())
    add_points("C-REG", 500, "grant")
    order = place_order(cart_with("C-REG", [("EL-200", 1), ("HM-100", 1)]), OK, ADDR, points_to_redeem=500)
    assert (order.loyalty_discount, order.points_redeemed, order.total) == (
        Decimal("5.00"), 500, Decimal("211.00"))
    assert balance("C-REG") == 200


def test_the_address_and_method_are_kept_on_the_order():
    order = place_order(cart_with("C-REG", [("BK-100", 1)]), OK, ADDR, "express")
    assert order.address == ADDR and order.shipping_method == "express" and order.shipping == Decimal("15.00")

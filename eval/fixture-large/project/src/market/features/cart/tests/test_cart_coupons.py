"""Tests for cart_coupons (CRT-06, PRM-01, PRM-04, PRM-06)."""
from datetime import date
from decimal import Decimal

import pytest

from market.features.cart.cart_coupons import apply_coupon, remove_coupon
from market.features.cart.cart_pricing import price_cart
from market.features.cart.cart_service import add_item, create_cart, get_cart
from market.features.catalog.product_store import add_product
from market.features.inventory.stock_store import set_on_hand
from market.features.promotions.coupon_store import add_coupon
from market.features.promotions.promotion_models import Coupon
from market.features.promotions.promotion_usage import hold_uses
from market.infra import clock
from market.infra.customers import add_customer
from market.infra.errors import PolicyError, ValidationError
from market.infra.models import Customer, Product


@pytest.fixture(autouse=True)
def world():
    add_customer(Customer("C-1", "one@example.com"))
    for sku, price in [("EL-200", "120.00"), ("HM-100", "80.00")]:
        add_product(Product(sku, sku, "home", Decimal(price), 100))
        set_on_hand(sku, 50)
    add_coupon(Coupon("SAVE10", "percent", Decimal("10"), min_subtotal=Decimal("50.00")))
    add_coupon(Coupon("SAVE20", "percent", Decimal("20"), min_subtotal=Decimal("100.00"),
                      per_customer_limit=1))
    add_coupon(Coupon("OLD", "percent", Decimal("5"), expires_on=date(2026, 1, 1)))


@pytest.fixture
def cart_id():
    cart = create_cart("C-1")
    add_item(cart.cart_id, "EL-200")
    add_item(cart.cart_id, "HM-100")
    return cart.cart_id


def test_apply_valid_coupon_stores_the_normalized_code(cart_id):
    apply_coupon(cart_id, " save10 ")
    assert get_cart(cart_id).coupon_codes == ["SAVE10"]


def test_reapplying_the_same_code_changes_nothing(cart_id):
    apply_coupon(cart_id, "SAVE10")
    apply_coupon(cart_id, "save10")
    assert get_cart(cart_id).coupon_codes == ["SAVE10"]


def test_unknown_coupon_is_refused_with_its_reason(cart_id):
    with pytest.raises(ValidationError) as caught:
        apply_coupon(cart_id, "NOPE")
    assert caught.value.message == "unknown"
    assert get_cart(cart_id).coupon_codes == []


def test_coupon_below_minimum_is_refused():
    empty = create_cart("C-1").cart_id
    with pytest.raises(ValidationError) as caught:
        apply_coupon(empty, "SAVE10")
    assert caught.value.message == "below_minimum"


def test_expired_coupon_is_refused(cart_id):
    with pytest.raises(ValidationError) as caught:
        apply_coupon(cart_id, "OLD")
    assert caught.value.message == "expired"


def test_coupon_over_the_customer_limit_is_refused(cart_id):
    hold_uses("ORD-1", "C-1", ["SAVE20"])
    with pytest.raises(ValidationError) as caught:
        apply_coupon(cart_id, "SAVE20")
    assert caught.value.message == "customer_limit_reached"


def test_second_coupon_of_the_same_kind_is_kept_but_loses_in_the_quote(cart_id):
    apply_coupon(cart_id, "SAVE10")
    apply_coupon(cart_id, "SAVE20")
    quote = price_cart(cart_id)
    assert quote.rejected_coupons == (("SAVE20", "kind_already_applied"),)
    assert quote.discount_total == Decimal("20.00")


def test_remove_coupon(cart_id):
    apply_coupon(cart_id, "SAVE10")
    remove_coupon(cart_id, "save10")
    remove_coupon(cart_id, "SAVE10")
    assert get_cart(cart_id).coupon_codes == []


def test_an_expired_cart_cannot_take_a_coupon(cart_id):
    clock.advance(days=8)
    with pytest.raises(PolicyError):
        apply_coupon(cart_id, "SAVE10")

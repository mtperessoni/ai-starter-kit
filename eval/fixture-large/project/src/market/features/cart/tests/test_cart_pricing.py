"""Tests for cart_pricing (PRC-01, PRC-02, PRC-06 through a cart)."""
from decimal import Decimal

import pytest

from market.features.cart.cart_coupons import apply_coupon
from market.features.cart.cart_pricing import price_cart
from market.features.cart.cart_service import add_item, create_cart
from market.features.catalog.product_store import add_product, update_price
from market.features.inventory.stock_store import set_on_hand
from market.features.promotions.coupon_store import add_coupon
from market.features.promotions.promotion_models import Coupon
from market.infra.customers import add_customer
from market.infra.errors import NotFoundError
from market.infra.models import Customer, Product


@pytest.fixture(autouse=True)
def world():
    add_customer(Customer("C-1", "one@example.com"))
    add_product(Product("EL-200", "Headphones", "electronics", Decimal("120.00"), 300))
    add_product(Product("HM-100", "Desk Lamp", "home", Decimal("80.00"), 1500))
    set_on_hand("EL-200", 5)
    set_on_hand("HM-100", 50)


def test_empty_cart_quotes_zero():
    quote = price_cart(create_cart("C-1").cart_id)
    assert quote.total == Decimal("0") and quote.lines == ()


def test_cart_quote_uses_current_prices_and_cart_coupons():
    add_coupon(Coupon("SAVE10", "percent", Decimal("10"), min_subtotal=Decimal("50.00")))
    cart_id = create_cart("C-1").cart_id
    add_item(cart_id, "EL-200")
    add_item(cart_id, "HM-100")
    apply_coupon(cart_id, "SAVE10")
    assert price_cart(cart_id).total == Decimal("180.00")
    update_price("HM-100", Decimal("100.00"))
    assert price_cart(cart_id).subtotal == Decimal("220.00")


def test_unknown_cart_raises_not_found():
    with pytest.raises(NotFoundError):
        price_cart("CRT-9999")

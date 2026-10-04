"""CHK-01, CHK-02, CHK-03, CHK-04, CHK-05, CHK-06, CHK-07: checkout."""

from decimal import Decimal

import pytest

from orders import Cart, CartItem, Coupon, Customer, Receipt, checkout

D = Decimal


def cart(*prices_and_qty):
    return Cart([CartItem(f"sku-{i}", D(p), q) for i, (p, q) in enumerate(prices_and_qty)])


def test_plain_order_pays_shipping():
    """CHK-01, CHK-02: total is subtotal minus discount plus shipping."""
    receipt = checkout(cart(("40.00", 2)), Customer("c1"))
    assert receipt == Receipt(D("80.00"), D("0.00"), D("15.00"), D("95.00"))


def test_vip_order_with_coupon():
    """CHK-01, CHK-02"""
    receipt = checkout(cart(("100.00", 1)), Customer("c1", vip=True), Coupon("TEN", D("10")))
    assert receipt == Receipt(D("100.00"), D("25.00"), D("15.00"), D("90.00"))


def test_large_order_ships_free():
    """CHK-01, SHP-02: a large order has no shipping."""
    receipt = checkout(cart(("300.00", 1)), Customer("c1"))
    assert receipt.shipping == D("0.00")
    assert receipt.total == D("300.00")


def test_discount_is_rounded_half_up_to_cents():
    """CHK-01: 15% of 10.05 is 1.5075, which rounds to 1.51."""
    receipt = checkout(cart(("10.05", 1)), Customer("c1", vip=True))
    assert receipt.discount == D("1.51")
    assert receipt.total == D("23.54")


def test_same_sku_lines_are_added():
    """CHK-01"""
    items = Cart([CartItem("a", D("10.00"), 1), CartItem("a", D("10.00"), 2)])
    assert checkout(items, Customer("c1")).subtotal == D("30.00")


def test_receipt_amounts_are_decimals():
    """CHK-02"""
    receipt = checkout(cart(("10.00", 1)), Customer("c1"))
    assert all(isinstance(v, Decimal) for v in (receipt.subtotal, receipt.discount, receipt.shipping, receipt.total))


def test_empty_cart_is_rejected():
    """CHK-03"""
    with pytest.raises(ValueError):
        checkout(Cart([]), Customer("c1"))


@pytest.mark.parametrize("qty", [0, -1])
def test_quantity_must_be_at_least_one(qty):
    """CHK-04"""
    with pytest.raises(ValueError):
        checkout(cart(("10.00", qty)), Customer("c1"))


def test_negative_price_is_rejected():
    """CHK-04"""
    with pytest.raises(ValueError):
        checkout(cart(("-1.00", 1)), Customer("c1"))


@pytest.mark.parametrize("percent", ["0", "-5", "101"])
def test_coupon_percent_must_be_between_zero_and_one_hundred(percent):
    """CHK-05"""
    with pytest.raises(ValueError):
        checkout(cart(("10.00", 1)), Customer("c1"), Coupon("BAD", D(percent)))


def test_customer_id_is_required():
    """CHK-06"""
    with pytest.raises(ValueError):
        checkout(cart(("10.00", 1)), Customer(""))


def test_receipt_text_has_four_labelled_lines():
    """CHK-07"""
    text = checkout(cart(("40.00", 1)), Customer("c1")).render().splitlines()
    assert [line.split(":")[0] for line in text] == ["Subtotal", "Discount", "Shipping", "Total"]
    assert text[-1].endswith("55.00")

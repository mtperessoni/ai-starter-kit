"""PRC-01, PRC-02, PRC-03, PRC-04: discount rules."""

from decimal import Decimal

from orders.features.pricing import compute_discount
from orders.infra.cart_models import Coupon, Customer

D = Decimal


def test_regular_customer_without_coupon_gets_nothing():
    """PRC-01: only VIP customers get the VIP discount."""
    assert compute_discount(D("100"), Customer("c1")) == D("0")


def test_vip_gets_fifteen_percent():
    """PRC-01"""
    assert compute_discount(D("100"), Customer("c1", vip=True)) == D("15")


def test_coupon_gives_its_percentage():
    """PRC-02"""
    assert compute_discount(D("200"), Customer("c1"), Coupon("TEN", D("10"))) == D("20")


def test_vip_and_coupon_add_up():
    """PRC-04: the percentages are added before the cap."""
    assert compute_discount(D("100"), Customer("c1", vip=True), Coupon("TEN", D("10"))) == D("25")


def test_discount_is_capped_at_thirty_percent():
    """PRC-03"""
    assert compute_discount(D("100"), Customer("c1", vip=True), Coupon("BIG", D("50"))) == D("30")


def test_discount_exactly_at_the_cap_is_not_reduced():
    """PRC-03"""
    assert compute_discount(D("100"), Customer("c1", vip=True), Coupon("FIFTEEN", D("15"))) == D("30")

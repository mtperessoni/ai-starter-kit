"""SHP-01, SHP-02: shipping fee."""

from decimal import Decimal

from orders.features.shipping import shipping_fee

D = Decimal


def test_small_order_pays_the_flat_fee():
    """SHP-01"""
    assert shipping_fee(D("50.00")) == D("15.00")


def test_just_below_the_threshold_pays_the_fee():
    """SHP-02"""
    assert shipping_fee(D("199.99")) == D("15.00")


def test_well_above_the_threshold_is_free():
    """SHP-02"""
    assert shipping_fee(D("250.00")) == D("0.00")


def test_zero_amount_still_pays_the_fee():
    """SHP-01"""
    assert shipping_fee(D("0.00")) == D("15.00")

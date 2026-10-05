"""Hidden tests for L2: product reviews (REV-01 to REV-05).

Only the public API is used.
"""
from decimal import Decimal as D

import pytest

from market import api

ADDR = api.Address("BR", "SP", "01000-000")
OK = api.PaymentRequest("card", "ok_1")


def _setup():
    api.reset()
    api.seed_demo()


def _buy(customer, sku="BK-100", qty=1, deliver=True):
    cart = api.create_cart(customer)
    api.add_to_cart(cart, sku, qty)
    order = api.place_order(cart, OK, ADDR)
    if deliver:
        api.mark_shipped(order.order_id)
        order = api.mark_delivered(order.order_id)
    return order


def test_delivered_buyer_can_review():
    """REV-01: a customer with a delivered order containing the SKU can review it."""
    _setup()
    _buy("C-REG")
    r = api.submit_review("C-REG", "BK-100", 5, "great")
    assert r.customer_id == "C-REG"
    assert r.sku == "BK-100"
    assert r.rating == 5
    assert r.text == "great"
    assert r.verified is True


def test_non_buyer_is_refused():
    """REV-01: no order, a paid-only order, or an order of another SKU gives PolicyError."""
    _setup()
    with pytest.raises(api.PolicyError):
        api.submit_review("C-REG", "BK-100", 5)
    _buy("C-REG", "BK-100", deliver=False)
    with pytest.raises(api.PolicyError):
        api.submit_review("C-REG", "BK-100", 5)
    _buy("C-VIP", "BK-200")
    with pytest.raises(api.PolicyError):
        api.submit_review("C-VIP", "BK-100", 5)


def test_partially_refunded_order_can_review():
    """REV-01: a partially refunded order still qualifies."""
    _setup()
    order = _buy("C-REG", "BK-100", qty=2)
    api.request_return(order.order_id, [("BK-100", 1)], "changed_mind")
    assert api.get_order(order.order_id).status == "partially_refunded"
    assert api.submit_review("C-REG", "BK-100", 4).rating == 4


def test_rating_out_of_range_is_invalid():
    """REV-02: ratings 0 and 6 and a text of 501 characters raise ValidationError; 500 is fine."""
    _setup()
    _buy("C-REG")
    with pytest.raises(api.ValidationError):
        api.submit_review("C-REG", "BK-100", 6)
    with pytest.raises(api.ValidationError):
        api.submit_review("C-REG", "BK-100", 0)
    with pytest.raises(api.ValidationError):
        api.submit_review("C-REG", "BK-100", 3, "x" * 501)
    assert len(api.submit_review("C-REG", "BK-100", 3, "x" * 500).text) == 500


def test_resubmit_replaces_and_keeps_id():
    """REV-03: a second submission replaces the first and keeps the review id."""
    _setup()
    _buy("C-REG")
    first = api.submit_review("C-REG", "BK-100", 5, "good")
    second = api.submit_review("C-REG", "BK-100", 2, "changed my mind")
    assert second.review_id == first.review_id
    reviews = api.list_reviews("BK-100")
    assert len(reviews) == 1
    assert reviews[0].rating == 2


def test_average_of_5_and_4_is_4_5():
    """REV-04: the mean of 5 and 4 is 4.5."""
    _setup()
    _buy("C-REG")
    _buy("C-VIP")
    api.submit_review("C-REG", "BK-100", 5)
    api.submit_review("C-VIP", "BK-100", 4)
    assert api.average_rating("BK-100") == D("4.5")


def test_average_of_5_4_4_is_4_3():
    """REV-04: 13 / 3 = 4.333 rounds to 4.3."""
    _setup()
    for customer, rating in (("C-REG", 5), ("C-VIP", 4), ("C-RJ", 4)):
        _buy(customer)
        api.submit_review(customer, "BK-100", rating)
    assert api.average_rating("BK-100") == D("4.3")


def test_average_rounds_half_up():
    """REV-04: 5, 4, 4, 4 average 4.25 and round half up to 4.3."""
    _setup()
    for customer, rating in (("C-REG", 5), ("C-VIP", 4), ("C-RJ", 4), ("C-AM", 4)):
        _buy(customer)
        api.submit_review(customer, "BK-100", rating)
    assert api.average_rating("BK-100") == D("4.3")


def test_average_without_reviews_is_none():
    """REV-04: no reviews means no average."""
    _setup()
    assert api.average_rating("BK-100") is None


def test_reviews_are_listed_newest_first():
    """REV-05: the review created last comes first."""
    _setup()
    _buy("C-REG")
    _buy("C-VIP")
    api.submit_review("C-REG", "BK-100", 5)
    api.advance_time(minutes=5)
    api.submit_review("C-VIP", "BK-100", 3)
    assert [r.customer_id for r in api.list_reviews("BK-100")] == ["C-VIP", "C-REG"]

"""Hidden tests for L7: VIP customers have 60 days to return, standard 30.

Rule ID: RET-01. Only the public API is used.
"""
import pytest

from market import api

ADDR = api.Address("BR", "SP", "01000-000")
OK = api.PaymentRequest("card", "ok_1")


def _delivered(customer, days):
    api.reset()
    api.seed_demo()
    cart = api.create_cart(customer)
    api.add_to_cart(cart, "BK-100", 1)
    order = api.place_order(cart, OK, ADDR)
    api.mark_shipped(order.order_id)
    api.mark_delivered(order.order_id)
    api.advance_time(days=days)
    return order.order_id


def test_vip_return_at_25_days_completes():
    """RET-01: inside 30 days a VIP can return."""
    oid = _delivered("C-VIP", 25)
    assert api.request_return(oid, [("BK-100", 1)], "changed_mind").status == "completed"


def test_standard_return_at_25_days_completes():
    """RET-01: inside 30 days a standard customer can return."""
    oid = _delivered("C-REG", 25)
    assert api.request_return(oid, [("BK-100", 1)], "changed_mind").status == "completed"


def test_vip_return_at_45_days_completes():
    """RET-01: a VIP has 60 days, so day 45 is accepted."""
    oid = _delivered("C-VIP", 45)
    assert api.request_return(oid, [("BK-100", 1)], "changed_mind").status == "completed"


def test_standard_return_at_45_days_is_refused():
    """RET-01: a standard customer has 30 days, so day 45 raises PolicyError."""
    oid = _delivered("C-REG", 45)
    with pytest.raises(api.PolicyError):
        api.request_return(oid, [("BK-100", 1)], "changed_mind")


def test_standard_return_at_31_days_is_refused():
    """RET-01: day 31 is outside the standard window."""
    oid = _delivered("C-REG", 31)
    with pytest.raises(api.PolicyError):
        api.request_return(oid, [("BK-100", 1)], "changed_mind")


def test_vip_return_at_61_days_is_refused():
    """RET-01: day 61 is outside the VIP window."""
    oid = _delivered("C-VIP", 61)
    with pytest.raises(api.PolicyError):
        api.request_return(oid, [("BK-100", 1)], "changed_mind")

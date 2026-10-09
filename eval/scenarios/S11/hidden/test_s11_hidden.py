"""Hidden tests for S11 (orders side): the receipt carries the customer name as received.

Rule ID is illustrative: CHK-02 (the receipt). The storefront side is checked in its own folder.
Only the public API is used.
"""
from decimal import Decimal as D

from orders import Cart, CartItem, Coupon, Customer, checkout


def _cart(price="100.00"):
    return Cart([CartItem("sku-1", D(price), 1)])


def test_the_receipt_carries_the_name_as_received():
    """CHK-02"""
    assert checkout(_cart(), Customer("c1", name="Ana")).customer_name == "Ana"


def test_no_name_gives_an_empty_string():
    """CHK-02"""
    assert checkout(_cart(), Customer("c1")).customer_name == ""


def test_the_name_is_not_split_or_trimmed_by_orders():
    """CHK-02: orders echoes what the storefront sent."""
    assert checkout(_cart(), Customer("c1", name="Ana Maria")).customer_name == "Ana Maria"


def test_vip_flag_and_name_work_together():
    """PRC-01: a VIP named Ana still gets 15% off."""
    r = checkout(_cart(), Customer("c1", vip=True, name="Ana"))
    assert r.discount == D("15.00")
    assert r.customer_name == "Ana"


def test_the_receipt_text_and_as_dict_do_not_change():
    """CHK-07"""
    r = checkout(_cart(), Customer("c1", name="Ana"), Coupon("TEN", D("10")))
    assert set(r.as_dict()) == {"subtotal", "discount", "shipping", "total"}
    assert "Ana" not in r.render()
    assert [line.split(":")[0].strip() for line in r.render().splitlines() if line.strip()] == [
        "Subtotal", "Discount", "Shipping", "Total"]


def test_totals_are_unchanged():
    """CHK-01: 100.00 for a regular customer: shipping 15.00, total 115.00."""
    r = checkout(_cart(), Customer("c1", name="Ana"))
    assert r.total == D("115.00")

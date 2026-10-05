"""Hidden tests for S2: store credit.

Rule IDs are illustrative: CRD-01..CRD-03 (new), CHK-01 (total), CHK-02 (receipt).
Only the public API is used.
"""
from decimal import Decimal as D

import orders
from orders import Cart, CartItem, Customer, checkout


def _cart(price="100.00", qty=1):
    return Cart([CartItem("sku-1", D(price), qty)])


def test_partial_credit_reduces_total():
    """CRD-02, CHK-01: 100.00 + 15.00 shipping = 115.00, credit 10.00 leaves 105.00."""
    r = checkout(_cart(), Customer("c1", store_credit_balance=D("10.00")))
    assert r.store_credit_used == D("10.00")
    assert r.total == D("105.00")


def test_credit_is_capped_at_order_amount():
    """CRD-02: balance 500.00 pays only 115.00, total is 0.00."""
    r = checkout(_cart(), Customer("c1", store_credit_balance=D("500.00")))
    assert r.store_credit_used == D("115.00")
    assert r.total == D("0.00")


def test_balance_equal_to_order_amount():
    """CRD-02: balance exactly 115.00 pays the whole order."""
    r = checkout(_cart(), Customer("c1", store_credit_balance=D("115.00")))
    assert r.store_credit_used == D("115.00")
    assert r.total == D("0.00")


def test_no_credit_changes_nothing():
    """CRD-01, CHK-02: default balance is zero, store_credit_used is 0.00, total is 115.00."""
    r = checkout(_cart(), Customer("c1"))
    assert r.store_credit_used == D("0.00")
    assert r.total == D("115.00")


def test_credit_applies_after_discounts_and_shipping():
    """CRD-02: VIP 100.00 - 15.00 + 15.00 = 100.00; balance 100.00 covers all of it."""
    r = checkout(_cart(), Customer("c1", vip=True, store_credit_balance=D("100.00")))
    assert r.discount == D("15.00")
    assert r.shipping == D("15.00")
    assert r.store_credit_used == D("100.00")
    assert r.total == D("0.00")


def test_checkout_does_not_change_balance():
    """CRD-03: checkout alone leaves the balance untouched."""
    c = Customer("c1", store_credit_balance=D("50.00"))
    checkout(_cart(), c)
    assert c.store_credit_balance == D("50.00")


def test_confirm_decreases_balance_by_used_amount():
    """CRD-03: confirming a receipt that used 115.00 of 200.00 leaves 85.00."""
    c = Customer("c1", store_credit_balance=D("200.00"))
    r = checkout(_cart(), c)
    orders.confirm(r, c)
    assert c.store_credit_balance == D("85.00")


def test_confirm_without_credit_leaves_balance():
    """CRD-03: a receipt that used no credit does not touch a zero balance."""
    c = Customer("c1")
    r = checkout(_cart(), c)
    orders.confirm(r, c)
    assert c.store_credit_balance == D("0")

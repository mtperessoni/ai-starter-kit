"""ORD-01: an order needs at least one item."""

from src.orders import create_order, cancel_order


def test_create():
    assert create_order([1])
    cancel_order(None)

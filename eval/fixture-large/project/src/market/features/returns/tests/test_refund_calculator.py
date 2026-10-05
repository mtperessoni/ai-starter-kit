"""Tests for refund_calculator (RET-03, RET-04): proration and the shipping refund."""
from decimal import Decimal

from market.features.returns.refund_calculator import compute_refund, prorate
from market.features.returns.tests.helpers import make_order, order_line


def test_merchandise_is_the_line_total_over_quantity_times_units():
    order = make_order([order_line("EL-200", "electronics", 3, "288.00", "23.04")])
    refund = compute_refund(order, [("EL-200", 1)], "changed_mind")
    assert (refund.merchandise, refund.tax, refund.total) == (
        Decimal("96.00"), Decimal("7.68"), Decimal("103.68"))


def test_proration_rounds_half_up_to_cents():
    assert prorate(Decimal("100.00"), 3, 1) == Decimal("33.33")
    assert prorate(Decimal("100.00"), 3, 2) == Decimal("66.67")
    assert prorate(Decimal("1.00"), 8, 1) == Decimal("0.13")


def test_several_lines_are_summed():
    order = make_order([order_line("EL-200", "electronics", 2, "200.00", "16.00"),
                        order_line("BK-100", "books", 1, "40.00")])
    refund = compute_refund(order, [("EL-200", 1), ("BK-100", 1)], "other")
    assert (refund.merchandise, refund.tax) == (Decimal("140.00"), Decimal("8.00"))


def test_shipping_is_refunded_when_defective_goods_complete_the_return():
    order = make_order([order_line("BK-100", "books", 2, "80.00")], shipping="10.00")
    refund = compute_refund(order, [("BK-100", 2)], "defective")
    assert refund.shipping == Decimal("10.00") and refund.total == Decimal("90.00")


def test_shipping_is_refunded_for_a_wrong_item():
    order = make_order([order_line("BK-100", "books", 1, "40.00")], shipping="10.00")
    assert compute_refund(order, [("BK-100", 1)], "wrong_item").shipping == Decimal("10.00")


def test_shipping_is_not_refunded_for_changed_mind_or_other():
    order = make_order([order_line("BK-100", "books", 1, "40.00")], shipping="10.00")
    assert compute_refund(order, [("BK-100", 1)], "changed_mind").shipping == Decimal("0.00")
    assert compute_refund(order, [("BK-100", 1)], "other").shipping == Decimal("0.00")


def test_shipping_is_not_refunded_for_a_partial_return():
    order = make_order([order_line("BK-100", "books", 2, "80.00")], shipping="10.00")
    assert compute_refund(order, [("BK-100", 1)], "defective").shipping == Decimal("0.00")


def test_shipping_counts_units_returned_before():
    order = make_order([order_line("BK-100", "books", 2, "80.00")], shipping="10.00",
                       status="partially_refunded", returned={"BK-100": 1})
    assert compute_refund(order, [("BK-100", 1)], "wrong_item").shipping == Decimal("10.00")


def test_shipping_waits_for_every_line_of_the_order():
    order = make_order([order_line("BK-100", "books", 1, "40.00"),
                        order_line("EL-200", "electronics", 1, "120.00", "9.60")], shipping="10.00")
    assert compute_refund(order, [("BK-100", 1)], "defective").shipping == Decimal("0.00")

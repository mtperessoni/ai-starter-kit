"""Tests for order_models (CHK-08, LOY-01, LOY-03): statuses, unit counters, points base."""
from datetime import datetime
from decimal import Decimal

from market.features.checkout.order_models import (STATUSES, Order, OrderLine, check_totals, merchandise_points_base,
                                                  order_summary)


def line(sku, category, qty, total):
    amount = Decimal(total)
    return OrderLine(sku, category, qty, amount / qty, amount, Decimal("0.00"), amount, Decimal("0.00"), 100)


def order(lines):
    zero = Decimal("0.00")
    return Order("ORD-0001", "C-REG", tuple(lines), zero, zero, zero, zero, zero, zero, "paid", None,
                 "standard", (), 0, None, None, None, datetime(2026, 3, 10, 12, 0))


def test_there_are_eight_statuses():
    assert STATUSES == ("pending", "paid", "payment_failed", "cancelled", "shipped", "delivered",
                        "partially_refunded", "refunded")


def test_units_bought_sums_lines_of_the_same_sku():
    placed = order([line("EL-200", "electronics", 2, "240.00"), line("EL-200", "electronics", 1, "120.00")])
    assert placed.units_bought("EL-200") == 3 and placed.units_bought("XX-000") == 0


def test_units_left_to_return_subtracts_returned_units():
    placed = order([line("EL-200", "electronics", 3, "360.00")])
    placed.returned_units["EL-200"] = 2
    assert placed.units_left_to_return("EL-200") == 1


def test_points_base_skips_gift_cards():
    lines = (line("EL-200", "electronics", 1, "120.00"), line("GC-050", "gift_card", 1, "50.00"))
    assert merchandise_points_base(lines) == Decimal("120.00")


def test_points_base_of_nothing_is_zero():
    assert merchandise_points_base(()) == Decimal("0.00")


def priced_order(total="140.40", discount="0.00"):
    zero = Decimal("0.00")
    item = OrderLine("EL-200", "electronics", 1, Decimal("120.00"), Decimal("120.00"), Decimal(discount),
                     Decimal("120.00") - Decimal(discount), Decimal("9.60"), 300)
    return Order("ORD-0001", "C-REG", (item,), Decimal("120.00"), Decimal(discount), Decimal("10.00"),
                 Decimal("10.40"), zero, Decimal(total), "paid", None, "standard", (), 0, None, None, None,
                 datetime(2026, 3, 10, 12, 0))


def test_check_totals_accepts_consistent_numbers():
    assert check_totals(priced_order()) == []


def test_check_totals_names_each_problem():
    problems = check_totals(priced_order(total="150.00", discount="5.00"))
    assert problems == ["total should be 135.40"]


def test_order_summary_lists_lines_and_money():
    assert order_summary(priced_order()) == [
        "ORD-0001 paid", "1 x EL-200 120.00", "shipping 10.00 / tax 10.40 / total 140.40"]

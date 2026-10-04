"""Tests for tax_calculator (TAX-02, TAX-03, TAX-04, TAX-05)."""
from decimal import Decimal

from market.features.pricing.quote_models import LineQuote
from market.features.tax.tax_calculator import (compute_tax, effective_rate, explain_tax, line_tax,
                                                    taxable_base)

ZERO = Decimal("0.00")


def line(total, sku="EL-200", category="electronics", qty=1, klass="standard", discount="0.00"):
    amount = Decimal(total)
    subtotal = amount + Decimal(discount)
    return LineQuote(sku, category, qty, subtotal / qty, subtotal, Decimal(discount), amount, klass, 100)


def test_tax_is_the_rate_on_the_line_total_after_discounts():
    assert compute_tax([line("96.00", discount="24.00")], ZERO, "SP").total == Decimal("7.68")


def test_each_line_is_rounded_before_summing():
    lines = [line("10.05", "EL-100"), line("10.05", "EL-200")]
    result = compute_tax(lines, ZERO, "SP")
    assert result.per_line == {"EL-100": Decimal("0.80"), "EL-200": Decimal("0.80")}
    assert result.total == Decimal("1.60")


def test_rounding_is_half_up():
    assert compute_tax([line("12.50")], ZERO, "MG").total == Decimal("1.13")


def test_exempt_categories_pay_no_tax():
    books = line("40.00", "BK-100", "books", klass="exempt")
    gift = line("50.00", "GC-050", "gift_card", klass="exempt")
    assert compute_tax([books, gift], ZERO, "SP").total == ZERO


def test_exempt_class_is_enough_even_for_a_standard_category():
    assert line_tax(line("100.00", klass="exempt"), Decimal("8")) == ZERO


def test_mixed_lines_tax_only_the_standard_ones():
    result = compute_tax([line("100.00"), line("40.00", "BK-100", "books", klass="exempt")], ZERO, "RJ")
    assert result.total == Decimal("10.00") and result.per_line["BK-100"] == ZERO


def test_shipping_is_taxed_at_the_same_rate():
    result = compute_tax([line("200.00")], Decimal("16.00"), "SP")
    assert result.shipping_tax == Decimal("1.28") and result.total == Decimal("17.28")


def test_free_shipping_has_no_tax():
    assert compute_tax([line("200.00")], ZERO, "SP").shipping_tax == ZERO


def test_shipping_is_taxed_even_when_every_line_is_exempt():
    result = compute_tax([line("40.00", "BK-100", "books", klass="exempt")], Decimal("10.00"), "SP")
    assert result.total == Decimal("0.80")


def test_tax_exempt_customer_pays_nothing():
    result = compute_tax([line("200.00")], Decimal("16.00"), "SP", tax_exempt=True)
    assert result.total == ZERO and result.shipping_tax == ZERO and result.per_line["EL-200"] == ZERO


def test_tax_is_added_on_top_and_leaves_the_line_untouched():
    item = line("100.00")
    result = compute_tax([item], ZERO, "SP")
    assert item.line_total == Decimal("100.00") and result.total == Decimal("8.00")


def test_result_carries_the_rate_used():
    assert compute_tax([line("10.00")], ZERO, "AM").rate == Decimal("7")


def test_same_sku_on_two_lines_is_summed():
    result = compute_tax([line("10.00"), line("20.00")], ZERO, "RJ")
    assert result.per_line["EL-200"] == Decimal("3.00")


def test_empty_order_has_no_tax():
    assert compute_tax([], ZERO, "SP").total == ZERO


def test_taxable_base_leaves_out_exempt_lines_and_exempt_customers():
    lines = [line("100.00"), line("40.00", "BK-100", "books", klass="exempt")]
    assert taxable_base(lines) == Decimal("100.00")
    assert taxable_base(lines, tax_exempt=True) == ZERO


def test_effective_rate_is_tax_over_base():
    result = compute_tax([line("200.00")], Decimal("16.00"), "SP")
    assert effective_rate(result, Decimal("216.00")) == Decimal("8.00")
    assert effective_rate(result, ZERO) == ZERO


def test_explain_tax_lists_taxed_items_shipping_and_rate():
    result = compute_tax([line("200.00"), line("40.00", "BK-100", "books", klass="exempt")], Decimal("16.00"), "SP")
    assert explain_tax(result) == ["EL-200 16.00", "shipping 1.28", "rate 8%"]

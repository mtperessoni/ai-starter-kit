"""Tests for price_calculator (PRC-01, PRC-02, PRC-03, PRC-04, PRC-06 and the quote of PRM-02, PRM-07)."""
from datetime import date
from decimal import Decimal

import pytest

from market.features.catalog.product_store import add_product, update_price
from market.features.pricing.price_calculator import line_subtotal, quote_lines
from market.features.promotions.coupon_store import add_category_sale, add_coupon
from market.features.promotions.promotion_models import CategorySale, Coupon
from market.infra.errors import NotFoundError
from market.infra.models import CartLine, Customer, Product

CUSTOMER = Customer("C-1", "one@example.com")


def D(value):
    return Decimal(value)


@pytest.fixture(autouse=True)
def catalog():
    for sku, name, category, price, weight in [
        ("EL-100", "USB Cable", "electronics", "15.00", 100),
        ("EL-200", "Headphones", "electronics", "120.00", 300),
        ("HM-100", "Desk Lamp", "home", "80.00", 1500),
        ("TY-100", "Puzzle", "toys", "30.00", 700),
        ("TY-200", "Blocks", "toys", "10.00", 100),
        ("TY-300", "Cards", "toys", "10.00", 100),
        ("TY-400", "Kite", "toys", "10.00", 100),
        ("OD-100", "Odd Item", "home", "1.11", 100),
        ("BK-100", "Python Basics", "books", "40.00", 400),
        ("GC-050", "Gift Card 50", "gift_card", "50.00", 0),
    ]:
        add_product(Product(sku, name, category, D(price), weight))


def quote(lines, codes=(), today=None):
    return quote_lines([CartLine(s, q) for s, q in lines], CUSTOMER, codes, today)


def test_line_subtotal_is_price_times_quantity():
    assert line_subtotal(D("15.00"), 3) == D("45.00")


def test_empty_cart_quotes_zero_everywhere():
    q = quote([])
    assert (q.subtotal, q.discount_total, q.total) == (D("0"), D("0"), D("0"))
    assert q.lines == () and q.discounts == () and not q.free_shipping


def test_subtotal_is_sum_of_line_subtotals_at_current_price():
    q = quote([("EL-200", 1), ("HM-100", 2)])
    assert [l.line_subtotal for l in q.lines] == [D("120.00"), D("160.00")]
    assert q.subtotal == D("280.00") and q.total == D("280.00")


def test_quote_carries_catalog_facts_for_tax_and_shipping():
    line = quote([("BK-100", 2)]).lines[0]
    assert (line.category, line.taxable_class, line.weight_grams, line.unit_price) == (
        "books", "exempt", 400, D("40.00"))


def test_quote_uses_the_price_of_now():
    update_price("EL-100", D("20.00"))
    assert quote([("EL-100", 1)]).subtotal == D("20.00")


def test_unknown_sku_raises_not_found():
    with pytest.raises(NotFoundError):
        quote([("NOPE-1", 1)])


def test_volume_break_five_percent_from_ten_units():
    q = quote([("EL-100", 10)])
    assert q.lines[0].line_discount == D("7.50") and q.lines[0].line_total == D("142.50")
    assert q.discounts[0].code == "VOLUME" and q.discounts[0].kind == "volume"


def test_volume_break_ten_percent_from_fifty_units_and_none_below_ten():
    assert quote([("EL-100", 50)]).discount_total == D("75.00")
    assert quote([("EL-100", 9)]).discount_total == D("0")


def test_volume_break_rounds_half_up():
    assert quote([("OD-100", 10)]).discount_total == D("0.56")


def test_gift_cards_get_no_volume_break():
    assert quote([("GC-050", 10)]).discount_total == D("0")


def test_percent_coupon_applies_after_volume_break():
    add_coupon(Coupon("SAVE10", "percent", D("10"), min_subtotal=D("50.00")))
    q = quote([("EL-100", 10)], ["SAVE10"])
    assert q.discount_total == D("21.75") and q.total == D("128.25")
    assert [d.kind for d in q.discounts] == ["volume", "percent_coupon"]


def test_coupon_on_two_lines_matches_the_seed_example():
    add_coupon(Coupon("SAVE10", "percent", D("10"), min_subtotal=D("50.00")))
    q = quote([("EL-200", 1), ("HM-100", 1)], ["SAVE10"])
    assert q.discount_total == D("20.00") and q.total == D("180.00")


def test_rejected_coupons_are_listed_with_their_reason():
    add_coupon(Coupon("SAVE20", "percent", D("20"), min_subtotal=D("100.00")))
    q = quote([("EL-100", 2)], ["SAVE20", "NOPE"])
    assert q.rejected_coupons == (("SAVE20", "below_minimum"), ("NOPE", "unknown"))
    assert q.total == q.subtotal


def test_shared_discount_adds_up_exactly_per_line():
    add_coupon(Coupon("FIX10", "fixed", D("10.00")))
    q = quote([("TY-200", 1), ("TY-300", 1), ("TY-400", 1)], ["FIX10"])
    assert [l.line_discount for l in q.lines] == [D("3.33"), D("3.33"), D("3.34")]
    assert sum(l.line_discount for l in q.lines) == q.discount_total == D("10.00")


def test_line_totals_add_up_to_the_quote_total():
    add_coupon(Coupon("SAVE10", "percent", D("10")))
    q = quote([("EL-100", 10), ("HM-100", 1), ("GC-050", 1)], ["SAVE10"])
    assert sum(l.line_total for l in q.lines) == q.total
    assert q.total == q.subtotal - q.discount_total


def test_gift_card_line_keeps_its_full_price_under_a_coupon():
    add_coupon(Coupon("SAVE10", "percent", D("10")))
    q = quote([("HM-100", 1), ("GC-050", 1)], ["SAVE10"])
    assert q.lines[1].line_discount == D("0") and q.lines[1].line_total == D("50.00")


def test_category_sale_uses_the_given_day():
    add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    assert quote([("TY-100", 1)], today=date(2026, 3, 10)).discount_total == D("6.00")
    assert quote([("TY-100", 1)], today=date(2026, 4, 2)).discount_total == D("0")


def test_default_day_is_the_clock_day():
    add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    assert quote([("TY-100", 1)]).discount_total == D("6.00")


def test_free_shipping_coupon_sets_the_flag_only():
    add_coupon(Coupon("FREESHIP", "free_shipping", D("0"), min_subtotal=D("30.00")))
    q = quote([("TY-100", 1)], ["FREESHIP"])
    assert q.free_shipping and q.discount_total == D("0") and q.total == D("30.00")

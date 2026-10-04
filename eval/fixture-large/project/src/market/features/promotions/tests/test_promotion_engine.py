"""Tests for promotion_engine (PRM-02, PRM-05 to PRM-13): each stage alone and the allowed pairs."""
from datetime import date
from decimal import Decimal

import pytest

from market.features.promotions import coupon_store as store
from market.features.promotions import promotion_engine as engine
from market.features.promotions.promotion_models import (BogoRule, Bundle, CategorySale, Coupon,
                                                         PromoLine)
from market.infra import config
from market.infra.errors import ValidationError
from market.infra.models import Customer

TODAY = date(2026, 3, 10)
CUSTOMER = Customer("C-1", "one@example.com")


def D(value):
    return Decimal(value)


def line(sku, category, qty, unit, value=None):
    unit = D(unit)
    return PromoLine(sku, category, qty, unit, D(value) if value is not None else unit * qty)


def run(lines, codes=(), today=TODAY):
    return engine.evaluate(lines, CUSTOMER, codes, today)


def percent(code="SAVE10", value="10", **kw):
    store.add_coupon(Coupon(code, "percent", D(value), **kw))


def fixed(code="FIX15", value="15.00", **kw):
    store.add_coupon(Coupon(code, "fixed", D(value), **kw))


def test_no_lines_gives_nothing():
    result = run([])
    assert result.discounts == () and result.total == D("0.00") and not result.free_shipping


def test_percent_coupon_takes_percent_of_value():
    percent(min_subtotal=D("50.00"))
    result = run([line("A-1", "toys", 1, "100.00")], ["SAVE10"])
    assert result.total == D("10.00")
    assert result.discounts[0].kind == "percent_coupon"
    assert result.applied_codes == ("SAVE10",)


def test_percent_coupon_below_minimum_is_rejected_not_failed():
    percent(min_subtotal=D("50.00"))
    result = run([line("A-1", "toys", 1, "40.00")], ["SAVE10"])
    assert result.total == D("0.00")
    assert result.rejected == (("SAVE10", "below_minimum"),)


def test_codes_ignore_case_and_spaces():
    percent()
    result = run([line("A-1", "toys", 1, "100.00")], ["  save10 "])
    assert result.total == D("10.00") and result.rejected == ()


def test_unknown_code_is_rejected():
    result = run([line("A-1", "toys", 1, "100.00")], ["NOPE"])
    assert result.rejected == (("NOPE", "unknown"),) and result.total == D("0.00")


def test_percent_rounds_half_up_once():
    percent()
    assert run([line("A-1", "toys", 1, "33.35")], ["SAVE10"]).total == D("3.34")


def test_percent_coupon_limited_to_categories():
    percent(categories=("toys",))
    lines = [line("T-1", "toys", 1, "60.00"), line("B-1", "books", 1, "40.00")]
    assert run(lines, ["SAVE10"]).total == D("6.00")


def test_gift_cards_are_never_discounted_nor_counted_for_minimum():
    percent(min_subtotal=D("50.00"))
    lines = [line("B-1", "books", 1, "100.00"), line("G-1", "gift_card", 1, "50.00")]
    result = run(lines, ["SAVE10"])
    assert result.total == D("10.00")
    assert all(sku != "G-1" for d in result.discounts for sku, _ in d.line_amounts)
    percent("BIG", "10", min_subtotal=D("120.00"))
    assert run(lines, ["BIG"]).rejected == (("BIG", "below_minimum"),)


def test_category_sale_takes_percent_of_its_category():
    store.add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    lines = [line("T-1", "toys", 1, "60.00"), line("B-1", "books", 1, "40.00")]
    result = run(lines)
    assert result.total == D("12.00") and result.discounts[0].kind == "category_sale"
    assert result.discounts[0].line_amounts == (("T-1", D("12.00")),)


@pytest.mark.parametrize("today,expected", [
    (date(2026, 3, 1), "12.00"), (date(2026, 3, 31), "12.00"),
    (date(2026, 2, 28), "0.00"), (date(2026, 4, 1), "0.00"),
])
def test_category_sale_window_includes_both_days(today, expected):
    store.add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    assert run([line("T-1", "toys", 1, "60.00")], today=today).total == D(expected)


def test_category_sale_never_touches_gift_cards():
    store.add_category_sale(CategorySale("SALE-GC", "gift_card", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    assert run([line("G-1", "gift_card", 1, "50.00")]).total == D("0.00")


@pytest.mark.parametrize("qty,expected", [(2, "0.00"), (3, "25.00"), (5, "25.00"), (6, "50.00")])
def test_bogo_gives_one_free_per_three(qty, expected):
    store.add_bogo(BogoRule("BOGO-TSHIRT", "FS-100"))
    assert run([line("FS-100", "fashion", qty, "25.00")]).total == D(expected)


def test_bogo_values_free_unit_at_current_value_per_unit():
    store.add_bogo(BogoRule("BOGO-TSHIRT", "FS-100"))
    result = run([line("FS-100", "fashion", 3, "25.00", value="60.00")])
    assert result.total == D("20.00") and result.discounts[0].kind == "bogo"


def test_fixed_coupon_takes_amount_off():
    fixed(min_subtotal=D("80.00"))
    result = run([line("A-1", "toys", 1, "100.00")], ["FIX15"])
    assert result.total == D("15.00") and result.discounts[0].kind == "fixed_coupon"


def test_fixed_coupon_below_minimum_is_rejected():
    fixed(min_subtotal=D("80.00"))
    assert run([line("A-1", "toys", 1, "60.00")], ["FIX15"]).rejected == (("FIX15", "below_minimum"),)


def test_fixed_coupon_never_exceeds_the_eligible_total():
    config.set("promo.max_total_discount_percent", D("100"))
    fixed("BIG50", "50.00")
    assert run([line("A-1", "toys", 1, "30.00")], ["BIG50"]).total == D("30.00")


def test_free_shipping_sets_flag_without_money():
    store.add_coupon(Coupon("FREESHIP", "free_shipping", D("0"), min_subtotal=D("30.00")))
    result = run([line("A-1", "toys", 1, "40.00")], ["FREESHIP"])
    assert result.free_shipping and result.total == D("0.00") and result.applied_codes == ("FREESHIP",)


def test_free_shipping_follows_the_same_validity_checks():
    store.add_coupon(Coupon("FREESHIP", "free_shipping", D("0"), min_subtotal=D("30.00")))
    lines = [line("A-1", "toys", 1, "20.00"), line("G-1", "gift_card", 1, "50.00")]
    result = run(lines, ["FREESHIP"])
    assert not result.free_shipping and result.rejected == (("FREESHIP", "below_minimum"),)


def test_second_coupon_of_a_kind_is_rejected():
    percent("SAVE10", "10")
    percent("SAVE20", "20")
    result = run([line("A-1", "toys", 1, "200.00")], ["SAVE10", "SAVE20"])
    assert result.total == D("20.00")
    assert result.rejected == (("SAVE20", "kind_already_applied"),)


def test_one_coupon_per_kind_allows_percent_and_fixed_together():
    percent()
    fixed()
    result = run([line("A-1", "toys", 1, "100.00")], ["SAVE10", "FIX15"])
    assert result.total == D("25.00") and result.applied_codes == ("SAVE10", "FIX15")


def test_pair_sale_then_percent_works_on_what_is_left():
    store.add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    percent()
    result = run([line("T-1", "toys", 1, "100.00")], ["SAVE10"])
    assert [d.amount for d in result.discounts] == [D("20.00"), D("8.00")]
    assert result.total == D("28.00")


def test_pair_bogo_then_percent_works_on_what_is_left():
    store.add_bogo(BogoRule("BOGO-TSHIRT", "FS-100"))
    percent(min_subtotal=D("50.00"))
    result = run([line("FS-100", "fashion", 3, "25.00")], ["SAVE10"])
    assert [d.amount for d in result.discounts] == [D("25.00"), D("5.00")]


def test_pair_percent_then_fixed_works_on_what_is_left():
    percent()
    fixed()
    result = run([line("A-1", "toys", 1, "100.00")], ["SAVE10", "FIX15"])
    assert [d.kind for d in result.discounts] == ["percent_coupon", "fixed_coupon"]
    assert result.discounts[1].amount == D("15.00")


def test_cap_cuts_a_step_to_what_is_left():
    store.add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    percent("BIG30", "30")
    result = run([line("T-1", "toys", 1, "100.00")], ["BIG30"])
    assert result.discounts[1].amount == D("20.00") and result.total == D("40.00")


def test_cap_ignores_gift_cards_in_its_base():
    percent("HALF", "50")
    lines = [line("B-1", "books", 1, "100.00"), line("G-1", "gift_card", 1, "100.00")]
    assert run(lines, ["HALF"]).total == D("40.00")


def test_cap_exhausted_leaves_later_stages_empty():
    store.add_category_sale(CategorySale("SALE-TOYS", "toys", D("40"), date(2026, 3, 1), date(2026, 3, 31)))
    percent()
    result = run([line("T-1", "toys", 1, "100.00")], ["SAVE10"])
    assert result.total == D("40.00") and result.applied_codes == ()


def test_cap_comes_from_config():
    config.set("promo.max_total_discount_percent", D("10"))
    percent("HALF", "50")
    assert run([line("A-1", "toys", 1, "100.00")], ["HALF"]).total == D("10.00")


def test_bundle_alone_gives_fixed_amount_split_by_value():
    store.add_bundle(Bundle("BUNDLE-READER", ("BK-100", "BK-200"), D("15.00")))
    result = run([line("BK-100", "books", 1, "40.00"), line("BK-200", "books", 1, "60.00")])
    assert result.total == D("15.00")
    assert result.discounts[0].line_amounts == (("BK-100", D("6.00")), ("BK-200", D("9.00")))


def test_bundle_counts_complete_sets():
    store.add_bundle(Bundle("BUNDLE-READER", ("BK-100", "BK-200"), D("15.00")))
    lines = [line("BK-100", "books", 3, "40.00"), line("BK-200", "books", 2, "60.00")]
    assert run(lines).total == D("30.00")


def test_bundle_needs_every_sku():
    store.add_bundle(Bundle("BUNDLE-READER", ("BK-100", "BK-200"), D("15.00")))
    assert run([line("BK-100", "books", 2, "40.00")]).discounts == ()


def test_bundle_never_exceeds_the_value_of_its_lines():
    config.set("promo.max_total_discount_percent", D("100"))
    store.add_bundle(Bundle("TINY", ("BK-100", "BK-200"), D("15.00")))
    assert run([line("BK-100", "books", 1, "8.00"), line("BK-200", "books", 1, "4.00")]).total == D("12.00")


def test_duplicate_sku_lines_are_rejected():
    with pytest.raises(ValidationError):
        run([line("A-1", "toys", 1, "10.00"), line("A-1", "toys", 1, "10.00")])


def test_invalid_line_is_rejected():
    with pytest.raises(ValidationError):
        run([line("A-1", "toys", 0, "10.00", value="0.00")])


def test_explain_has_one_line_per_discount():
    percent()
    result = run([line("A-1", "toys", 1, "100.00")], ["SAVE10"])
    assert engine.explain(result) == ["SAVE10 percent_coupon -10.00"]


def test_explain_rejections_gives_readable_reasons():
    result = run([line("A-1", "toys", 1, "100.00")], ["NOPE"])
    assert engine.explain_rejections(result) == ["NOPE: the code does not exist"]


def test_trace_reports_every_stage_and_matches_the_total():
    store.add_category_sale(CategorySale("SALE-TOYS", "toys", D("20"), date(2026, 3, 1), date(2026, 3, 31)))
    percent()
    lines = [line("T-1", "toys", 1, "100.00")]
    records = engine.trace(lines, CUSTOMER, ["SAVE10"], TODAY)
    assert len(records) == len(engine.PIPELINE)
    assert sum(r.taken for r in records) == run(lines, ["SAVE10"]).total
    assert engine.summarize(run(lines, ["SAVE10"])) == {
        "category_sale": D("20.00"), "percent_coupon": D("8.00")}

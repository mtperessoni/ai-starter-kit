"""PRM-02 to PRM-13: the promotion pipeline (sales, bogo, percent, bundle, fixed, free shipping, cap)."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from market.features.promotions.coupon_store import (active_sales, bogo_rules, bundles, find_coupon,
                                                     normalize_code)
from market.features.promotions.coupon_validation import check_coupon
from market.features.promotions.promotion_models import (AppliedDiscount, Coupon, PromoLine,
                                                         PromoResult)
from market.infra import config
from market.infra.errors import ValidationError
from market.infra.models import Customer
from market.infra.money import allocate, pct, q2

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ZERO = Decimal("0.00")

ELIGIBLE_EXCLUDED_CATEGORIES = ("gift_card",)

KIND_PERCENT = "percent"
KIND_FIXED = "fixed"
KIND_FREE_SHIPPING = "free_shipping"
COUPON_KINDS = (KIND_PERCENT, KIND_FIXED, KIND_FREE_SHIPPING)

DISCOUNT_CATEGORY_SALE = "category_sale"
DISCOUNT_BOGO = "bogo"
DISCOUNT_PERCENT_COUPON = "percent_coupon"
DISCOUNT_BUNDLE = "bundle"
DISCOUNT_FIXED_COUPON = "fixed_coupon"

REASON_UNKNOWN = "unknown"
REASON_KIND_TAKEN = "kind_already_applied"

CAP_CONFIG_KEY = "promo.max_total_discount_percent"

REASON_TEXT = {
    "unknown": "the code does not exist",
    "not_started": "the coupon has not started yet",
    "expired": "the coupon has expired",
    "below_minimum": "the eligible subtotal is below the coupon minimum",
    "limit_reached": "the coupon reached its global limit",
    "customer_limit_reached": "this customer already used the coupon as many times as allowed",
    REASON_KIND_TAKEN: "another coupon of the same kind already applies",
}

STAGE_RULES = {
    "stage_category_sales": "PRM-07",
    "stage_bogo": "PRM-08",
    "stage_percent_coupons": "PRM-02",
    "stage_bundles": "PRM-09",
    "stage_fixed_coupons": "PRM-10",
    "stage_free_shipping": "PRM-13",
}


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


@dataclass
class _Context:
    """Mutable state of one evaluation.

    `values` is the running value per sku: it starts at the value after the
    volume break and every stage lowers it by what the stage took, so the
    next stage works on what the previous ones left (PRM-05).
    `spent` is the engine discount taken so far, the number the cap (PRM-11)
    is measured against.

    Example: two lines worth 60.00 and 40.00 start with
    `values == {"A": 60.00, "B": 40.00}` and `spent == 0.00`.
    """

    lines: list[PromoLine]
    customer: Customer
    codes: list[str]
    today: date
    values: dict[str, Decimal] = field(default_factory=dict)
    discounts: list[AppliedDiscount] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)
    applied_codes: list[str] = field(default_factory=list)
    coupons: dict[str, Coupon] = field(default_factory=dict)
    free_shipping: bool = False
    eligible_list_subtotal: Decimal = ZERO
    spent: Decimal = ZERO

    def line_for(self, sku: str) -> PromoLine | None:
        for line in self.lines:
            if line.sku == sku:
                return line
        return None

    def remaining_value(self) -> Decimal:
        """Running value of every line, gift cards included."""
        return sum(self.values.values(), ZERO)

    def discount_total(self) -> Decimal:
        """Sum of the amounts recorded so far."""
        return sum((discount.amount for discount in self.discounts), ZERO)

    def taken_by_sku(self) -> dict[str, Decimal]:
        """Engine discount per sku, the sum of `line_amounts` of every discount."""
        taken: dict[str, Decimal] = {}
        for discount in self.discounts:
            for sku, amount in discount.line_amounts:
                taken[sku] = taken.get(sku, ZERO) + amount
        return taken

    def stage_count(self) -> int:
        """Number of discounts recorded so far."""
        return len(self.discounts)


def _validate_line(line: PromoLine) -> None:
    """Reject lines that would make the arithmetic meaningless.

    A line must have a positive integer quantity, a non negative unit price
    and a value between 0 and `unit_price * qty` (the volume break can only
    lower the value, never raise it).
    """
    if not isinstance(line.qty, int) or line.qty <= 0:
        raise ValidationError(f"line {line.sku}: quantity must be a positive integer")
    if line.unit_price < 0:
        raise ValidationError(f"line {line.sku}: unit price cannot be negative")
    if line.value < 0:
        raise ValidationError(f"line {line.sku}: value cannot be negative")
    if line.value > line.unit_price * line.qty:
        raise ValidationError(f"line {line.sku}: value exceeds the list subtotal")


def _validate_codes(codes: Sequence[str]) -> None:
    """Coupon codes must be strings; blanks are ignored later, never an error (PRM-01)."""
    if isinstance(codes, str):
        raise ValidationError("codes must be a sequence of strings, not one string")
    for code in codes:
        if not isinstance(code, str):
            raise ValidationError("coupon codes must be strings")


def _validate_inputs(lines: Sequence[PromoLine], codes: Sequence[str], today: date) -> None:
    """Check the whole input once, before any stage runs.

    Lines are checked one by one, a sku may appear only once (the running
    value is kept per sku), the date must be a date and every code a string.
    """
    if not isinstance(today, date):
        raise ValidationError("today must be a date")
    seen: set[str] = set()
    for line in lines:
        _validate_line(line)
        if line.sku in seen:
            raise ValidationError(f"line {line.sku} appears twice")
        seen.add(line.sku)
    _validate_codes(codes)


def _new_context(lines: Sequence[PromoLine], customer: Customer, codes: Sequence[str],
                 today: date) -> _Context:
    """Validate the inputs and build the starting context of an evaluation."""
    _validate_inputs(lines, codes, today)
    ctx = _Context(list(lines), customer, list(codes), today)
    ctx.values = {line.sku: line.value for line in ctx.lines}
    ctx.eligible_list_subtotal = _list_subtotal(_eligible(ctx))
    return ctx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _eligible(ctx: _Context) -> list[PromoLine]:
    """Lines a promotion may touch (PRM-12): everything except gift cards."""
    return [line for line in ctx.lines if line.category not in ELIGIBLE_EXCLUDED_CATEGORIES]


def _in_categories(lines: Sequence[PromoLine], categories: Sequence[str]) -> list[PromoLine]:
    """Keep the lines of the given categories; no categories means no restriction."""
    if not categories:
        return list(lines)
    return [line for line in lines if line.category in categories]


def _list_subtotal(lines: Sequence[PromoLine]) -> Decimal:
    """Sum of `unit_price * qty` before any discount, the base of minimums and the cap."""
    return sum((line.unit_price * line.qty for line in lines), ZERO)


def _value_of(ctx: _Context, lines: Sequence[PromoLine]) -> Decimal:
    """Current running value of the given lines."""
    return sum((ctx.values[line.sku] for line in lines), ZERO)


def _weights(ctx: _Context, lines: Sequence[PromoLine]) -> list[tuple[str, Decimal]]:
    """(sku, running value) pairs used to share a discount over lines (PRC-04)."""
    return [(line.sku, ctx.values[line.sku]) for line in lines]


def _percent_of(amount: Decimal, percent: Decimal) -> Decimal:
    """A percent of an amount rounded half up to cents, the rule for every stage total."""
    return q2(pct(amount, percent))


def _cap_limit(ctx: _Context) -> Decimal:
    """The most all promotions together may take (PRM-11).

    Example: eligible list subtotal 200.00 with a 40% cap gives 80.00. Gift
    cards are not in the eligible subtotal, so they never raise the cap.
    """
    return _percent_of(ctx.eligible_list_subtotal, config.get(CAP_CONFIG_KEY))


def _headroom(ctx: _Context) -> Decimal:
    """What the cap still allows (PRM-11), never below zero.

    Example: eligible list subtotal 200.00 and a 40% cap give 80.00; after
    50.00 was taken the headroom is 30.00.
    """
    allowed = _cap_limit(ctx) - ctx.spent
    return allowed if allowed > 0 else ZERO


def _trim(ctx: _Context, amount: Decimal) -> Decimal:
    """Cut an amount to what the cap still allows (PRM-11)."""
    if amount <= 0:
        return ZERO
    return min(amount, _headroom(ctx))


def _take(ctx: _Context, code: str, kind: str, amount: Decimal,
          weights: list[tuple[str, Decimal]]) -> None:
    """Record a discount: share it over the lines, lower their values, add to `spent`.

    The pieces come from `money.allocate`, so they add up to `amount` exactly
    (PRC-04). A zero amount records nothing.
    """
    if amount <= 0 or not weights:
        return
    pieces = allocate(amount, [weight for _, weight in weights])
    line_amounts: list[tuple[str, Decimal]] = []
    for (sku, _), piece in zip(weights, pieces):
        if piece <= 0:
            continue
        ctx.values[sku] = max(ZERO, ctx.values[sku] - piece)
        line_amounts.append((sku, piece))
    ctx.spent += amount
    ctx.discounts.append(AppliedDiscount(code, kind, amount, tuple(line_amounts)))


def _mark_applied(ctx: _Context, code: str) -> None:
    """Remember that a coupon gave something, so checkout can hold its use (PRM-04)."""
    if code not in ctx.applied_codes:
        ctx.applied_codes.append(code)


def _coupon_lines(ctx: _Context, coupon: Coupon) -> list[PromoLine]:
    """Eligible lines a coupon may discount, narrowed to its categories (PRM-02)."""
    return _in_categories(_eligible(ctx), coupon.categories)


# ---------------------------------------------------------------------------
# Coupon intake
# ---------------------------------------------------------------------------


def _reject(ctx: _Context, code: str, reason: str) -> None:
    ctx.rejected.append((code, reason))


def _resolve_coupons(ctx: _Context) -> None:
    """Pick the coupon of each kind that will apply (PRM-01, 03, 04, 06, 13).

    Codes ignore case and surrounding spaces. Each code is checked with
    `check_coupon` against the list subtotal of the lines it may discount.
    The first valid coupon of a kind wins; a later valid one of the same kind
    is rejected as `kind_already_applied`. A rejected coupon never fails the
    evaluation, it is only listed with its reason.

    Example: ["save10", " SAVE20 "] with both percent coupons valid gives
    `coupons == {"percent": SAVE10}` and `rejected == [("SAVE20",
    "kind_already_applied")]`.

    The same code given twice is looked at once. A coupon that is invalid for
    its own reason keeps that reason even if another coupon of its kind
    already won, so the customer sees the real problem first.
    """
    seen: set[str] = set()
    for raw in ctx.codes:
        code = normalize_code(raw)
        if not code or code in seen:
            continue
        seen.add(code)
        coupon = find_coupon(code)
        if coupon is None:
            _reject(ctx, code, REASON_UNKNOWN)
            continue
        if coupon.kind not in COUPON_KINDS:
            _reject(ctx, code, REASON_UNKNOWN)
            continue
        base = _list_subtotal(_coupon_lines(ctx, coupon))
        reason = check_coupon(code, base, ctx.customer.customer_id, ctx.today)
        if reason is not None:
            _reject(ctx, code, reason)
            continue
        if coupon.kind in ctx.coupons:
            _reject(ctx, code, REASON_KIND_TAKEN)
            continue
        ctx.coupons[coupon.kind] = coupon


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


def _sale_applies(percent: Decimal, starts_on: date, ends_on: date, today: date) -> bool:
    """Defensive recheck of a sale window; the store already filters by date."""
    if not Decimal("0") < percent <= Decimal("100"):
        return False
    return starts_on <= today <= ends_on


def stage_category_sales(ctx: _Context) -> None:
    """PRM-07: a category sale takes its percent off every eligible line of its category.

    The sale runs from its start date to its end date, both days included.
    The percent is applied once to the current value of all the lines of the
    category and the total is rounded half up to cents, then shared over the
    lines. Several sales are applied one after the other.

    Example: toys sale 20% on a line worth 60.00 takes 12.00 and leaves 48.00.

    Worked case with two toys lines (PRM-07, PRC-04):

        line  value  share
        T-1   30.00   30%
        T-2   70.00   70%

    20% of 100.00 is 20.00, so T-1 gets 6.00 and T-2 gets 14.00. A sale of a
    category with no line in the cart records nothing, and a gift card line
    is never in `eligible`, so a sale of its category would skip it (PRM-12).
    """
    eligible = _eligible(ctx)
    for sale in active_sales(ctx.today):
        if not _sale_applies(sale.percent, sale.starts_on, sale.ends_on, ctx.today):
            continue
        lines = _in_categories(eligible, (sale.category,))
        if not lines:
            continue
        amount = _trim(ctx, q2(pct(_value_of(ctx, lines), sale.percent)))
        _take(ctx, sale.sale_id, DISCOUNT_CATEGORY_SALE, amount, _weights(ctx, lines))


def _unit_value(ctx: _Context, line: PromoLine) -> Decimal:
    """Current value of one unit of a line, rounded half up to cents (PRM-08)."""
    return q2(ctx.values[line.sku] / line.qty)


def _free_units(qty: int, buy: int, free: int) -> int:
    """Units given for free: `free` for every complete group of `buy + free` units."""
    group = buy + free
    if group <= 0:
        return 0
    return (qty // group) * free


def stage_bogo(ctx: _Context) -> None:
    """PRM-08: buy 2 get 1 free.

    For every complete group of three units of the rule's SKU one unit is
    free, valued at the line's current value per unit (rounded half up to
    cents). Remaining units pay in full.

    Example: 4 units of a 25.00 shirt are one group, so 25.00 is free; 6 units
    are two groups and 50.00 is free.

    Worked case after a category sale (PRM-05): 3 shirts of 25.00 listed at
    75.00 whose value fell to 60.00 are worth 20.00 per unit, so the free
    unit is valued at 20.00, not at 25.00. The amount can never exceed the
    current value of the line and is cut by the cap like any other step.
    """
    eligible = {line.sku: line for line in _eligible(ctx)}
    for rule in bogo_rules():
        line = eligible.get(rule.sku)
        if line is None:
            continue
        free_units = _free_units(line.qty, rule.buy, rule.free)
        if free_units <= 0:
            continue
        amount = q2(_unit_value(ctx, line) * free_units)
        amount = _trim(ctx, min(amount, ctx.values[line.sku]))
        _take(ctx, rule.rule_id, DISCOUNT_BOGO, amount, [(line.sku, ctx.values[line.sku])])


def stage_percent_coupons(ctx: _Context) -> None:
    """PRM-02: a percent coupon takes its percent off the eligible lines.

    The base is the current value of the eligible lines (restricted to the
    coupon's categories when it has some). The percent is rounded half up to
    cents once for the whole coupon. The minimum was already checked against
    the eligible list subtotal when the coupon was resolved.

    Example: SAVE10 on 100.00 of current value takes 10.00; on 33.35 it takes
    3.34 (3.335 rounded half up).

    Worked case with a category limit (PRM-02, PRM-12): a coupon limited to
    "toys" on a cart of 60.00 of toys and 40.00 of books takes its percent
    of 60.00 only. Gift cards are never part of the base. If the cap leaves
    less than the percent, the coupon takes what is left and still counts
    as applied; if the cap leaves nothing it records nothing and its use is
    not held.
    """
    coupon = ctx.coupons.get(KIND_PERCENT)
    if coupon is None:
        return
    lines = _coupon_lines(ctx, coupon)
    if not lines:
        return
    amount = _trim(ctx, q2(pct(_value_of(ctx, lines), coupon.value)))
    if amount <= 0:
        return
    _take(ctx, coupon.code, DISCOUNT_PERCENT_COUPON, amount, _weights(ctx, lines))
    _mark_applied(ctx, coupon.code)


def _complete_sets(ctx: _Context, skus: Sequence[str]) -> tuple[int, list[PromoLine]]:
    """Number of complete sets of a bundle and the lines that form it.

    Sets are the smallest quantity among the bundle SKUs; a SKU that is not
    in the cart (or is not eligible) makes the number of sets zero.
    """
    eligible = {line.sku: line for line in _eligible(ctx)}
    members: list[PromoLine] = []
    for sku in skus:
        line = eligible.get(sku)
        if line is None:
            return 0, []
        members.append(line)
    return min(line.qty for line in members), members


def stage_bundles(ctx: _Context) -> None:
    """PRM-09: a bundle gives a fixed amount off for every complete set.

    The amount is `sets * amount_off`, never more than the current value of
    the bundle lines, and it is shared over those lines in proportion to
    their value.

    Example: BK-100 + BK-200 with 15.00 off and one of each (100.00) takes
    15.00; with 2 of the first and 1 of the second there is still one set.

    Worked cases (PRM-09):

        cart                          sets  amount
        BK-100 x1, BK-200 x1          1     15.00
        BK-100 x3, BK-200 x2          2     30.00
        BK-100 x1                     0     none (BK-200 missing)
        values 8.00 + 4.00, 15.00 off 1     12.00 (never above the value)

    Each stage works on the value the previous stages left, which is why the
    order of `PIPELINE` decides the final amount (PRM-05).
    """
    for bundle in bundles():
        sets, members = _complete_sets(ctx, bundle.skus)
        if sets <= 0:
            continue
        amount = q2(min(bundle.amount_off * sets, _value_of(ctx, members)))
        amount = _trim(ctx, amount)
        _take(ctx, bundle.bundle_id, DISCOUNT_BUNDLE, amount, _weights(ctx, members))


def stage_fixed_coupons(ctx: _Context) -> None:
    """PRM-10: a fixed coupon takes its amount off the current eligible total.

    The minimum was checked when the coupon was resolved. The amount is never
    more than the current total of the lines it may discount.

    Example: FIX15 on 75.00 of current value takes 15.00; on 10.00 of current
    value it takes only 10.00.

    Worked case (PRM-10, PRM-11): 120.00 of list subtotal with a 40% cap
    allows 48.00 in total. If the earlier stages already took 40.00, FIX15
    is cut to 8.00 and the cap is reached; the following stages find no
    headroom and record nothing.
    """
    coupon = ctx.coupons.get(KIND_FIXED)
    if coupon is None:
        return
    lines = _coupon_lines(ctx, coupon)
    if not lines:
        return
    amount = _trim(ctx, q2(min(coupon.value, _value_of(ctx, lines))))
    if amount <= 0:
        return
    _take(ctx, coupon.code, DISCOUNT_FIXED_COUPON, amount, _weights(ctx, lines))
    _mark_applied(ctx, coupon.code)


def stage_free_shipping(ctx: _Context) -> None:
    """PRM-13: a valid free-shipping coupon only sets the flag.

    It follows the same validity checks as any coupon and gives no money
    discount; the checkout passes the flag to shipping.

    Worked case (PRM-13): FREESHIP has a 30.00 minimum. A cart with 25.00 of
    products and a 50.00 gift card has an eligible subtotal of 25.00, so the
    coupon is rejected as `below_minimum` and the flag stays False. With
    35.00 of products the coupon is accepted, `free_shipping` is True and
    the discount total is still 0.00.
    """
    coupon = ctx.coupons.get(KIND_FREE_SHIPPING)
    if coupon is None:
        return
    ctx.free_shipping = True
    _mark_applied(ctx, coupon.code)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

PIPELINE: tuple[Callable[[_Context], None], ...] = (
    stage_category_sales,
    stage_bogo,
    stage_bundles,
    stage_percent_coupons,
    stage_fixed_coupons,
    stage_free_shipping,
)


def evaluate(lines: Sequence[PromoLine], customer: Customer, codes: Sequence[str],
             today: date) -> PromoResult:
    """Run every promotion over the lines and return what was taken (PRM-05).

    Coupons are resolved once, then each stage of `PIPELINE` runs on what the
    previous stages left. The total is the sum of the discount amounts and
    never exceeds the cap (PRM-11).

    Example: one 100.00 line with SAVE10 gives one `percent_coupon` discount
    of 10.00 and `total == 10.00`.
    """
    ctx = _new_context(lines, customer, codes, today)
    _resolve_coupons(ctx)
    for stage in PIPELINE:
        stage(ctx)
        _check_invariants(ctx, stage.__name__)
    return _result_of(ctx)


def _result_of(ctx: _Context) -> PromoResult:
    """Freeze a context into the value handed back to pricing."""
    return PromoResult(
        discounts=tuple(ctx.discounts),
        total=ctx.discount_total(),
        free_shipping=ctx.free_shipping,
        rejected=tuple(ctx.rejected),
        applied_codes=tuple(ctx.applied_codes),
    )


# ---------------------------------------------------------------------------
# Self checks
# ---------------------------------------------------------------------------


def _check_invariants(ctx: _Context, stage_name: str) -> None:
    """Fail loudly if a stage broke the arithmetic the rules promise.

    After every stage: no running value is negative, `spent` equals the sum
    of the recorded amounts, the cap (PRM-11) is respected and every
    discount's line pieces add up to its amount (PRC-04).
    """
    for sku, value in ctx.values.items():
        if value < 0:
            raise ValidationError(f"{stage_name}: value of {sku} went negative")
    if ctx.spent != ctx.discount_total():
        raise ValidationError(f"{stage_name}: spent does not match the recorded discounts")
    if ctx.spent > _cap_limit(ctx):
        raise ValidationError(f"{stage_name}: the discount cap was exceeded")
    for discount in ctx.discounts:
        pieces = sum((amount for _, amount in discount.line_amounts), ZERO)
        if pieces != discount.amount:
            raise ValidationError(f"{stage_name}: {discount.code} pieces do not add up")


# ---------------------------------------------------------------------------
# Reading the result
# ---------------------------------------------------------------------------


def explain(result: PromoResult) -> list[str]:
    """One line per discount: `<code> <kind> -<amount>`."""
    return [f"{d.code} {d.kind} -{d.amount}" for d in result.discounts]


def explain_rejections(result: PromoResult) -> list[str]:
    """One line per rejected coupon with a readable reason (PRM-01, PRC-06).

    Example: `("SAVE20", "below_minimum")` becomes
    `"SAVE20: the eligible subtotal is below the coupon minimum"`.
    """
    lines = []
    for code, reason in result.rejected:
        lines.append(f"{code}: {REASON_TEXT.get(reason, reason)}")
    return lines


def summarize(result: PromoResult) -> dict[str, Decimal]:
    """Total taken per discount kind, for reports and tests.

    Example: a sale of 12.00 and a percent coupon of 8.00 give
    `{"category_sale": 12.00, "percent_coupon": 8.00}`.
    """
    totals: dict[str, Decimal] = {}
    for discount in result.discounts:
        totals[discount.kind] = totals.get(discount.kind, ZERO) + discount.amount
    return totals


def describe_pipeline() -> list[str]:
    """The stages in the order they run, each with the rule it implements."""
    return [f"{position}. {stage.__name__} ({STAGE_RULES.get(stage.__name__, '?')})"
            for position, stage in enumerate(PIPELINE, start=1)]


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StageRecord:
    """What one stage did: how much it took and what the cap still allowed after it."""

    stage: str
    rule: str
    taken: Decimal
    headroom_after: Decimal
    remaining_value: Decimal


def trace(lines: Sequence[PromoLine], customer: Customer, codes: Sequence[str],
          today: date) -> list[StageRecord]:
    """Run the pipeline like `evaluate` and report each stage, for debugging a quote.

    Example: a 100.00 line with SAVE10 and a 15.00 bundle gives one record per
    stage; the percent coupon record shows `taken == 10.00` and the bundle
    record shows what the bundle took from the value left after the coupon.
    """
    ctx = _new_context(lines, customer, codes, today)
    _resolve_coupons(ctx)
    records: list[StageRecord] = []
    for stage in PIPELINE:
        before = ctx.spent
        stage(ctx)
        _check_invariants(ctx, stage.__name__)
        records.append(StageRecord(
            stage=stage.__name__,
            rule=STAGE_RULES.get(stage.__name__, "?"),
            taken=ctx.spent - before,
            headroom_after=_headroom(ctx),
            remaining_value=ctx.remaining_value(),
        ))
    return records

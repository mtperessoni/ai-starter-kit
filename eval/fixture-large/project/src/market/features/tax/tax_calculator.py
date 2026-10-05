"""TAX-02, TAX-03, TAX-04, TAX-05: tax per line and on shipping, added on top of the price."""
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from market.features.catalog.category_rules import EXEMPT_CATEGORIES
from market.features.pricing.quote_models import LineQuote
from market.features.tax.tax_rates import rate_for
from market.infra.money import pct, q2

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class TaxResult:
    total: Decimal
    per_line: dict[str, Decimal] = field(default_factory=dict)
    shipping_tax: Decimal = ZERO
    rate: Decimal = Decimal("0")


def _is_exempt(line: LineQuote) -> bool:
    return line.taxable_class == "exempt" or line.category in EXEMPT_CATEGORIES


def line_tax(line: LineQuote, rate: Decimal) -> Decimal:
    """Tax of one line: the rate on the line total after discounts, rounded half up (TAX-03).

    A 96.00 electronics line at 8% pays 7.68. A book line pays 0.00 (TAX-02).
    """
    if _is_exempt(line):
        return ZERO
    return q2(pct(line.line_total, rate))


def compute_tax(lines: Sequence[LineQuote], shipping_fee: Decimal, region: str | None,
                tax_exempt: bool = False) -> TaxResult:
    """Tax of an order: each line rounded, then summed, plus tax on the shipping fee.

    A tax-exempt customer pays nothing at all (TAX-02). Free shipping has no tax (TAX-04).
    The result is added on top of prices, never included in them (TAX-05).

    Example, SP at 8%: lines 200.00 plus shipping 16.00 gives 16.00 + 1.28 = 17.28.
    """
    rate = rate_for(region)
    if tax_exempt:
        return TaxResult(ZERO, {line.sku: ZERO for line in lines}, ZERO, rate)
    per_line: dict[str, Decimal] = {}
    for line in lines:
        per_line[line.sku] = per_line.get(line.sku, ZERO) + line_tax(line, rate)
    shipping_tax = q2(pct(shipping_fee, rate)) if shipping_fee > 0 else ZERO
    total = sum(per_line.values(), ZERO) + shipping_tax
    return TaxResult(total, per_line, shipping_tax, rate)


def taxable_base(lines: Sequence[LineQuote], tax_exempt: bool = False) -> Decimal:
    """Sum of line totals that attract tax: standard lines of a customer who is not exempt."""
    if tax_exempt:
        return ZERO
    return sum((line.line_total for line in lines if not _is_exempt(line)), ZERO)


def effective_rate(result: TaxResult, base: Decimal) -> Decimal:
    """Tax over a base in percent, to two decimals; zero when the base is zero.

    Tax of 17.28 over a base of 216.00 gives 8.00.
    """
    if base <= 0:
        return ZERO
    return q2(result.total * 100 / base)


def explain_tax(result: TaxResult) -> list[str]:
    """One line per taxed item for receipts: `<sku> <amount>` then the shipping tax and the rate."""
    rows = [f"{sku} {amount}" for sku, amount in result.per_line.items() if amount > 0]
    if result.shipping_tax > 0:
        rows.append(f"shipping {result.shipping_tax}")
    rows.append(f"rate {result.rate.normalize():f}%")
    return rows

# TRD · tax

Regional rates and tax per line and on shipping. 1:1 map of `src/market/features/tax/`. May import pricing (models only) and catalog (`category_rules`).

Rules in the PRD (ID, file in `docs/prd/market/`): TAX-01..05 ([10](../prd/market/10-tax.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `compute_tax` | TAX-01..05 |
| `tax_rates.py` | Rates by region | `RATES`, `DEFAULT_RATE`, `rate_for` | TAX-01 |
| `tax_calculator.py` | Tax per line and on shipping | `TaxResult`, `compute_tax` | TAX-02..05 |

## How it enters the flow
1. `checkout/order_quote.py::build_quote` calls `compute_tax(lines, shipping_fee, region, tax_exempt)` after shipping is known.
2. The region is the address region, or the customer's region without an address.
3. The result feeds the order total and the per-line tax stored on `OrderLine`, which returns later use (RET-03).

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_tax_rates.py` | Rates and default | TAX-01 |
| `tests/test_tax_calculator.py` | Exempt, rounding, shipping, free shipping | TAX-02..05 |

## Must not break
- Tax uses the line total after the discount split (TAX-03, PRC-04).
- Exempt products and tax-exempt customers pay nothing (TAX-02).
- Free shipping has no tax (TAX-04).

## Known pitfalls
- Rounding per line, then sum; never round the sum.

## History
- 2026-03-10: created by trd-create from the seed commit.

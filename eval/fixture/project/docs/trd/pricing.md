# TRD · pricing

Computes the discount of a subtotal for a customer and an optional coupon. 1:1 map of `src/orders/features/pricing/`.

Rules in the PRD (ID, file in `docs/prd/orders/`): PRC-01..04 ([02](../prd/orders/02-pricing.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry | `compute_discount` | PRC-01..04 |
| `discount_calculator.py` | Adds the VIP and coupon percentages and applies the cap | `compute_discount` | PRC-01, PRC-02, PRC-03, PRC-04 |

## How it enters the flow
1. `checkout_flow.py::compute_rounded_discount` calls `compute_discount` with the rounded subtotal.
2. The result is unrounded; checkout rounds it.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_discount_calculator.py` | VIP, coupon, stacking, cap | PRC-01..04 |

## Must not break
- The discount never exceeds the cap (PRC-03).
- The percentages are added before the cap (PRC-04).

## Known pitfalls
- `compute_discount` returns an unrounded Decimal; rounding belongs to checkout (CHK-01).

## History
- 2026-01-05: created by trd-create from the seed commit.

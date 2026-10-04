# features/pricing · Pricing

Computes the discount of a subtotal for a customer and an optional coupon.

- Rules: PRC-01 to PRC-04 in `docs/prd/orders/02-pricing.md`; index in `docs/prd/INDEX.md`.
- Entry: `compute_discount` (`discount_calculator.py`), re-exported by `__init__.py`.
- Domain: percentages are added, then capped at 30% of the subtotal; the result is not rounded.

Must not break:
- the discount never exceeds the cap (PRC-03);
- the percentages are added before the cap (PRC-04).

Tests: `tests/` in this folder.

TRD: `docs/trd/pricing.md`

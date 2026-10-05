# TRD · promotions

Coupons, sales, buy-x-get-y, bundles and the discount engine. 1:1 map of `src/market/features/promotions/`. Imports no other feature.

Rules in the PRD (ID, file in `docs/prd/market/`): PRM-01..13 ([04](../prd/market/04-promotions.md)).

## Big file

`promotions/promotion_engine.py` is a big file (about 700 lines). Do not read it whole: read by symbol from the table below.

| Section | Symbols | IDs |
|---|---|---|
| Constants | `ELIGIBLE_EXCLUDED_CATEGORIES`, `KIND_PERCENT`, `KIND_FIXED`, `KIND_FREE_SHIPPING` | PRM-12 |
| Context | `_Context`, `_new_context` | none |
| Helpers | `_eligible`, `_list_subtotal`, `_headroom`, `_trim`, `_take` | PRM-11, PRM-12 |
| Coupon intake | `_resolve_coupons` | PRM-01, PRM-03, PRM-04, PRM-06, PRM-13 |
| Stages | `stage_category_sales`, `stage_bogo`, `stage_percent_coupons`, `stage_bundles`, `stage_fixed_coupons`, `stage_free_shipping` | PRM-07, PRM-08, PRM-02, PRM-09, PRM-10, PRM-13 |
| Pipeline | `PIPELINE`, `evaluate` | PRM-05 |
| Explain | `explain` | none |

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `evaluate` | PRM-05 |
| `promotion_models.py` | Dataclasses | `Coupon`, `CategorySale`, `BogoRule`, `Bundle`, `PromoLine`, `AppliedDiscount`, `PromoResult` | PRM-02, PRM-08, PRM-09 |
| `coupon_store.py` | Definitions of coupons, sales, rules, bundles | `add_coupon`, `get_coupon`, `find_coupon`, `add_category_sale`, `add_bogo`, `add_bundle`, `active_sales`, `bogo_rules`, `bundles`, `normalize_code` | PRM-01, PRM-07 |
| `promotion_usage.py` | Use accounting: hold, commit, release | `hold_uses`, `commit_uses`, `release_uses`, `usage_count` | PRM-04 |
| `coupon_validation.py` | Validity checks in order unknown, not_started, expired, below_minimum, limit_reached, customer_limit_reached | `check_coupon` | PRM-03, PRM-04 |
| `promotion_engine.py` | The big file: pure functions over `_Context` | `evaluate`, `explain`, `PIPELINE` | PRM-02, PRM-05..13 |

## How it enters the flow
1. `pricing/price_calculator.py::quote_lines` calls `evaluate(lines, customer, codes, today)`.
2. `evaluate` calls `_resolve_coupons` once, then each stage of `PIPELINE` in PRM-05 order, then returns a `PromoResult`.
3. `checkout/order_placement.py::place_order` calls `hold_uses` after the stock hold, `commit_uses` on capture; `_rollback` and `cancel_order` call `release_uses`.
4. `cart/cart_coupons.py::apply_coupon` calls `check_coupon`.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_promotion_engine.py` | Each stage alone and allowed pairs, cap, rejections | PRM-02, PRM-05..13 |
| `tests/test_coupon_store.py` | Definitions, normalize | PRM-01 |
| `tests/test_coupon_validation.py` | Dates, minimum, limits | PRM-03, PRM-04 |
| `tests/test_promotion_usage.py` | Hold, commit, release | PRM-04 |

## Must not break
- `PIPELINE` order is category sale, buy-x-get-y, percent coupon, bundle, fixed coupon, free shipping (PRM-05).
- The engine writes to no repository: usage accounting is `promotion_usage` only.
- Gift cards never enter a stage (PRM-12).
- Total engine discount stays within the cap (PRM-11).

## Known pitfalls
- Rounding happens once per stage total, through `money.allocate` in `_take`.

## History
- 2026-03-10: created by trd-create from the seed commit.

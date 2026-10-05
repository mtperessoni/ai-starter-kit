# TRD · cart

Lines, coupons and expiry of a cart. 1:1 map of `src/market/features/cart/`. May import catalog, inventory, pricing, promotions.

Rules in the PRD (ID, file in `docs/prd/market/`): CRT-01..07 ([06](../prd/market/06-cart.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `create_cart`, `add_item`, `price_cart` | CRT-01..07 |
| `cart_service.py` | Lines of a cart | `create_cart`, `get_cart`, `add_item`, `set_quantity`, `remove_item`, `clear_cart`, `mark_converted` | CRT-01..05 |
| `cart_coupons.py` | Coupons on a cart | `apply_coupon`, `remove_coupon` | CRT-06 |
| `cart_pricing.py` | Quote of a cart | `price_cart` | CRT-04 |
| `cart_expiry.py` | Expiry | `is_expired`, `purge_expired` | CRT-07 |

## How it enters the flow
1. `api.add_to_cart` calls `add_item`, which checks `catalog.require_sellable` and `inventory.available`.
2. `apply_coupon` calls `promotions.coupon_validation.check_coupon`.
3. `price_cart` looks up the customer and calls `pricing.quote_lines`.
4. `order_placement.place_order` loads the cart, checks `is_expired`, and ends with `mark_converted`.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_cart_service.py` | Quantities, limits, products, stock | CRT-01..05 |
| `tests/test_cart_coupons.py` | Apply, reapply, reject | CRT-06 |
| `tests/test_cart_pricing.py` | Quote through pricing | CRT-04 |
| `tests/test_cart_expiry.py` | Expiry and purge | CRT-07 |

## Must not break
- A cart stores no prices (PRC-01).
- An expired cart cannot be changed or bought (CRT-07).
- Reapplying a coupon changes nothing (CRT-06).

## Known pitfalls
- `cart.ttl_days` counts from `updated_at`; every change moves it.

## History
- 2026-03-10: created by trd-create from the seed commit.

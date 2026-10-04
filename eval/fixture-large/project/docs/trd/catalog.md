# TRD · catalog

Product facts, validation, storage and search. 1:1 map of `src/market/features/catalog/`. Imports no other feature.

Rules in the PRD (ID, file in `docs/prd/market/`): CAT-01..07 ([02](../prd/market/02-catalog.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `add_product`, `get_product`, `require_sellable` | CAT-04, CAT-05 |
| `category_rules.py` | Category facts: exempt, digital, returnable, stock tracked | `CATEGORIES`, `EXEMPT_CATEGORIES`, `is_digital`, `is_returnable`, `is_stock_tracked` | CAT-03 |
| `product_validation.py` | Validates a product and a price change | `validate_product`, `validate_price_change`, `taxable_class_for` | CAT-01, CAT-02, CAT-03, CAT-06 |
| `product_store.py` | Persistence and lookup | `add_product`, `get_product`, `find_product`, `list_products`, `require_sellable`, `deactivate_product`, `update_price` | CAT-04, CAT-05, CAT-06 |
| `catalog_search.py` | Search and sort | `search_products` | CAT-07 |

## How it enters the flow
1. `api.add_product` calls `product_store.add_product`, which runs `validate_product` and sets `taxable_class`.
2. `cart_service.add_item` and `order_placement.place_order` call `require_sellable`.
3. Pricing, shipping, tax and returns read `category_rules` (`is_digital`, `EXEMPT_CATEGORIES`, `is_returnable`).

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_product_validation.py` | SKU, name, price, category, weight, price change | CAT-01..03, CAT-06 |
| `tests/test_product_store.py` | Duplicate, deactivate, sellable | CAT-04, CAT-05 |
| `tests/test_catalog_search.py` | Match, sort, filters | CAT-07 |
| `tests/test_category_rules.py` | Category facts | CAT-03 |

## Must not break
- A deactivated product stays readable for past orders (CAT-05).
- `category_rules` is the only place that knows which categories are exempt, digital or returnable (CAT-03).

## Known pitfalls
- Config limits (`catalog.max_price`, `catalog.max_price_change_percent`) are read at call time, not import time.

## History
- 2026-03-10: created by trd-create from the seed commit.

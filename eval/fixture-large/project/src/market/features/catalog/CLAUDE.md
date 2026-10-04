# features/catalog · Catalog

Products, validation, storage and search. Imports no other feature.

- Rules: CAT-01 to CAT-07 in `docs/prd/market/02-catalog.md`; index in `docs/prd/INDEX.md`.
- Entry: `add_product`, `require_sellable` (`product_store.py`), `search_products` (`catalog_search.py`).
- Collaborators: `product_validation` (checks), `category_rules` (exempt, digital, returnable, tracked).
- Domain: `taxable_class` is set on add from the category.

Must not break:
- a deactivated product stays readable for past orders (CAT-05);
- `category_rules` is the only place that lists exempt categories (CAT-03).

Tests: `tests/` in this folder.

TRD: `docs/trd/catalog.md`

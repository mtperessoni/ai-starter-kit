# features/promotions · Promotions

Coupons, sales, buy-x-get-y, bundles and the discount engine. Imports no other feature.

- Rules: PRM-01 to PRM-13 in `docs/prd/market/04-promotions.md`; index in `docs/prd/INDEX.md`.
- Entry: `evaluate` (`promotion_engine.py`), re-exported by `__init__.py`.
- Big file: `promotion_engine.py` (about 700 lines). Read by symbol, never whole; the symbol table is in the TRD.
- Collaborators: `coupon_store`, `coupon_validation`, `promotion_usage` (hold, commit, release), `promotion_models`.
- Domain: `PIPELINE` order is the contract of PRM-05; the engine is pure and writes no repository.

Must not break:
- `PIPELINE` order: sale, buy-x-get-y, percent, bundle, fixed, free shipping (PRM-05);
- total engine discount within the cap (PRM-11); gift cards never discounted (PRM-12).

Tests: `tests/` in this folder.

TRD: `docs/trd/promotions.md`

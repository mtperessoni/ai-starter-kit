# features/inventory · Inventory

Stock levels, timed holds and stock events. May import catalog.

- Rules: INV-01 to INV-08 in `docs/prd/market/05-inventory.md`; index in `docs/prd/INDEX.md`.
- Entry: `reserve`, `release`, `commit` (`reservations.py`), `available` (`stock_store.py`).
- Collaborators: `low_stock` publishes `inventory.low_stock` and `inventory.restocked`.
- Domain: available = on hand minus active holds; gift cards are untracked.

Must not break:
- release is idempotent (INV-05);
- a reservation is all or nothing and names every short SKU (INV-03);
- gift cards are never reserved (INV-07).

Tests: `tests/` in this folder.

TRD: `docs/trd/inventory.md`

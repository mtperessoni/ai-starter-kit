# TRD · inventory

Stock levels, timed holds and stock events. 1:1 map of `src/market/features/inventory/`. May import catalog.

Rules in the PRD (ID, file in `docs/prd/market/`): INV-01..08 ([05](../prd/market/05-inventory.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `reserve`, `available` | INV-02, INV-03 |
| `stock_store.py` | Stock on hand, reserved and available | `set_on_hand`, `add_stock`, `on_hand`, `reserved`, `available` | INV-01, INV-02, INV-07, INV-08 |
| `reservations.py` | Holds and their lifecycle | `Reservation`, `reserve`, `release`, `commit`, `expire_due`, `get_reservation` | INV-03..06 |
| `low_stock.py` | Threshold event | `check_low_stock` | INV-08 |

## How it enters the flow
1. `cart_service.add_item` reads `available`.
2. `order_placement.place_order` calls `reserve`, then `commit` on capture; `_rollback` and `cancel_order` call `release`.
3. `add_stock` and `reserve`/`commit` call `check_low_stock`, which publishes `inventory.low_stock` and `inventory.restocked` (see [flow](../flow.md)).
4. `returns/return_service.py::request_return` calls `add_stock` for returned goods.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_stock_store.py` | On hand, available, untracked | INV-01, INV-02, INV-07 |
| `tests/test_reservations.py` | All or nothing, expiry, release, commit | INV-03..06 |
| `tests/test_low_stock.py` | Threshold and restock events | INV-08 |

## Must not break
- Release is idempotent (INV-05).
- A reservation is all or nothing (INV-03).
- Gift cards are never reserved (INV-07).

## Known pitfalls
- `inventory.reservation_minutes` is read when a reservation is created; changing it does not move existing expiries.

## History
- 2026-03-10: created by trd-create from the seed commit.

# TRD · loyalty

Points earned, redeemed, expired and taken back. 1:1 map of `src/market/features/loyalty/`. Peripheral: imports no feature, listens to events, and serves checkout through the port. Its `__init__.py` calls `register()` once at import.

Rules in the PRD (ID, file in `docs/prd/market/`): LOY-01..06 and the planned LOY-07 ([11](../prd/market/11-loyalty.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Calls `register()` at import | `register` | LOY-01 |
| `points_ledger.py` | Lots of points, FIFO spend, clawback, expiry | `PointsLot`, `add_points`, `balance`, `spend`, `claw_back`, `expire_lots` | LOY-05, LOY-06 |
| `points_earning.py` | Points for an order | `tier_multiplier`, `points_for_order` | LOY-01, LOY-02, LOY-07 (planned) |
| `points_redemption.py` | Redemption value and the port implementation | `redemption_value`, `LoyaltyRedemptionPort` | LOY-04 |
| `loyalty_events.py` | Event handlers | `on_order_paid`, `on_order_cancelled`, `on_return_completed`, `register` | LOY-01, LOY-03, LOY-06 |

## How it enters the flow
1. `api.py` wires `LoyaltyRedemptionPort` with `checkout.ports.set_loyalty_port`; checkout asks `redemption_value` in `build_quote`.
2. `order.paid` calls `on_order_paid`: earns points on `points_base`, spends `points_redeemed`.
3. `order.cancelled` calls `on_order_cancelled`: claws back earned points, returns redeemed ones.
4. `return.completed` calls `on_return_completed`: claws back points on `points_base_returned`.
5. LOY-07 is approved and not built: it will change `points_for_order` and the `on_order_paid` wiring.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_points_ledger.py` | Lots, FIFO, expiry, clawback floor | LOY-05, LOY-06 |
| `tests/test_points_earning.py` | Base, VIP multiplier | LOY-01, LOY-02 |
| `tests/test_points_redemption.py` | Step, minimum, caps | LOY-04 |
| `tests/test_loyalty_events.py` | Paid, cancelled, return, gift cards | LOY-03, LOY-06 |

## Must not break
- Core never imports loyalty; checkout reaches it only through the port.
- The balance never goes below zero on clawback (LOY-06).
- Gift cards earn no points (LOY-03).

## Known pitfalls
- `grant_points` in the api adds a lot with reason `grant`; it counts for expiry and is not a first order.

## History
- 2026-03-10: created by trd-create from the seed commit.

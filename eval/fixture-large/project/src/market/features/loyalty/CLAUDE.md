# features/loyalty · Loyalty

Points earned, redeemed, expired and taken back. Peripheral: imports no feature, reacts to events.

- Rules: LOY-01 to LOY-06 in `docs/prd/market/11-loyalty.md`; LOY-07 is approved and planned, not built.
- Entry: `register` (called once by `__init__.py`), `redemption_value` (`points_redemption.py`).
- Collaborators: `points_ledger` (lots), `points_earning`, `loyalty_events` (paid, cancelled, return).
- Domain: checkout reaches it only through `LoyaltyPort`; FIFO spend, expiry by lot.

Must not break:
- core never imports loyalty (port and events only);
- a clawback never goes below a zero balance (LOY-06);
- gift cards earn nothing (LOY-03).

Tests: `tests/` in this folder.

TRD: `docs/trd/loyalty.md`

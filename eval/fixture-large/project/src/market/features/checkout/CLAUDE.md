# features/checkout · Checkout

Quote, validation, placement and lifecycle of an order. Reaches loyalty only through `ports.py`.

- Rules: CHK-01 to CHK-10 in `docs/prd/market/07-checkout.md`; index in `docs/prd/INDEX.md`.
- Entry: `place_order` (`order_placement.py`), `cancel_order` (`order_lifecycle.py`), `build_quote` (`order_quote.py`).
- Collaborators: `order_validation`, `order_models`, `ports` (`LoyaltyPort`).
- Domain: sequence quote, validate, reserve, hold uses, create, charge, commit or `_rollback` (flow in `docs/flow.md`).

Must not break:
- the placement sequence (CHK-02);
- `_rollback` releases the stock hold and the coupon uses (CHK-06);
- a decline returns the order, it does not raise (CHK-06).

Tests: `tests/` in this folder.

TRD: `docs/trd/checkout.md`

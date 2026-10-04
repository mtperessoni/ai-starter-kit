# features/checkout · Checkout

Validates a request, computes the totals and builds the receipt.

- Rules: CHK-01 to CHK-07 in `docs/prd/orders/04-checkout.md`; index in `docs/prd/INDEX.md`.
- Entry: `checkout` and `Receipt` (`checkout_flow.py`), re-exported by `__init__.py` and by `orders`.
- Collaborators: `pricing.compute_discount`, `shipping.shipping_fee`, called through their public entries.
- Today `checkout_flow.py` holds validation, totals, rounding and the receipt in one module.

Must not break:
- every receipt amount is rounded half up to cents (CHK-01);
- `orders.checkout` and `orders.Receipt` keep their signatures (CHK-02).

Tests: `tests/` in this folder.

TRD: `docs/trd/checkout.md`

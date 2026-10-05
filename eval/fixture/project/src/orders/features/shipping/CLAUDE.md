# features/shipping · Shipping

Decides the shipping fee from the amount after discounts.

- Rules: SHP-01 and SHP-02 in `docs/prd/orders/03-shipping.md`; index in `docs/prd/INDEX.md`.
- Entry: `shipping_fee` (`shipping_fee.py`), re-exported by `__init__.py`.

Must not break:
- the fee is 15.00 below the free-shipping threshold (SHP-01);
- the threshold applies to the amount after discounts (SHP-02).

Tests: `tests/` in this folder.

TRD: `docs/trd/shipping.md`

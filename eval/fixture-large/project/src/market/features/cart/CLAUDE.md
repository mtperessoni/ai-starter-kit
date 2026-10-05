# features/cart · Cart

Lines, coupons and expiry of a cart. May import catalog, inventory, pricing, promotions.

- Rules: CRT-01 to CRT-07 in `docs/prd/market/06-cart.md`; index in `docs/prd/INDEX.md`.
- Entry: `add_item`, `set_quantity` (`cart_service.py`), `apply_coupon` (`cart_coupons.py`), `price_cart` (`cart_pricing.py`).
- Collaborators: `cart_expiry` (`is_expired`, `purge_expired`).
- Domain: a cart stores SKUs and quantities only; prices come from pricing.

Must not break:
- a cart never stores a price (PRC-01);
- an expired cart cannot be changed or bought (CRT-07);
- reapplying a coupon changes nothing (CRT-06).

Tests: `tests/` in this folder.

TRD: `docs/trd/cart.md`

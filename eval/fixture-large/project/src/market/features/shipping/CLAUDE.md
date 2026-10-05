# features/shipping · Shipping

Zones, weight surcharge, thresholds and methods. May import pricing (models only) and catalog (`category_rules`).

- Rules: SHP-01 to SHP-06 in `docs/prd/market/09-shipping.md`; index in `docs/prd/INDEX.md`.
- Entry: `quote_shipping` (`shipping_fee.py`).
- Collaborators: `shipping_zones` (tables), `shipping_rules` (digital only, weight, surcharge, threshold).
- Domain: waivers (threshold, coupon) apply to standard only; express is never free.

Must not break:
- a gift-card-only order has fee 0.00 and no days (SHP-04);
- express is never free (SHP-05);
- only physical lines count for weight (SHP-06).

Tests: `tests/` in this folder.

TRD: `docs/trd/shipping.md`

# TRD · shipping

Zones, weight surcharge, thresholds and methods. 1:1 map of `src/market/features/shipping/`. May import pricing (models only) and catalog (`category_rules`).

Rules in the PRD (ID, file in `docs/prd/market/`): SHP-01..06 ([09](../prd/market/09-shipping.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `quote_shipping`, `ShippingRequest` | SHP-01..06 |
| `shipping_zones.py` | Zone tables | `ZONE_BY_REGION`, `zone_for`, `BASE_FEE`, `STANDARD_DAYS`, `EXPRESS_DAYS` | SHP-01, SHP-06 |
| `shipping_rules.py` | Digital only, weight, surcharge, threshold | `is_digital_only`, `total_weight`, `weight_surcharge`, `free_threshold` | SHP-02, SHP-03, SHP-04 |
| `shipping_fee.py` | The quote | `ShippingRequest`, `ShippingQuote`, `quote_shipping` | SHP-04, SHP-05, SHP-06 |

## How it enters the flow
1. `checkout/order_quote.py::build_quote` builds a `ShippingRequest` from the quote lines, merchandise after discounts, tier, method and the free-shipping flag from promotions (PRM-13).
2. `quote_shipping` returns fee, zone, days and free reason (`digital`, `threshold`, `coupon`).
3. The fee goes to `tax.compute_tax` as shipping to be taxed.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_shipping_zones.py` | Regions and zones | SHP-01 |
| `tests/test_shipping_rules.py` | Surcharge, thresholds, digital only | SHP-02..04 |
| `tests/test_shipping_fee.py` | Standard, express, waivers, weight limit, days | SHP-04..06 |

## Must not break
- Threshold and coupon waivers apply to standard only; express is never free (SHP-05, SHP-06).
- A gift-card-only order has fee 0.00 and no days (SHP-04).
- Only physical lines count for weight (SHP-06).

## Known pitfalls
- The threshold is read through `free_threshold(tier)` so the VIP value stays in one place.

## History
- 2026-03-10: created by trd-create from the seed commit.

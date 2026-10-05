# TRD · pricing

Quotes the lines of a cart: volume breaks, promotions, totals. 1:1 map of `src/market/features/pricing/`. May import catalog and promotions.

Rules in the PRD (ID, file in `docs/prd/market/`): PRC-01..06 ([03](../prd/market/03-pricing.md)); PRC-04 lives in `infra/money.py` ([infra](infra.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `quote_lines`, `PriceQuote` | PRC-01, PRC-02 |
| `quote_models.py` | Quote dataclasses | `LineQuote`, `PriceQuote` | PRC-06 |
| `volume_breaks.py` | Quantity breaks per line | `volume_percent`, `volume_discount` | PRC-03, PRC-05 |
| `discount_allocation.py` | Sums the per-line amounts of discounts | `line_discount_map` | PRC-04 |
| `price_calculator.py` | Builds the quote | `line_subtotal`, `quote_lines` | PRC-01, PRC-02, PRC-06 |

## How it enters the flow
1. `cart_pricing.price_cart` calls `quote_lines` with the cart lines, the customer and the coupon codes.
2. `quote_lines` applies the volume break, builds `PromoLine` values and calls `promotions.promotion_engine.evaluate`.
3. The discounts are spread to lines with `line_discount_map` (amounts split by `infra.money.allocate`) and the `PriceQuote` is returned.
4. `checkout/order_quote.py::build_quote` calls it again for the order.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_price_calculator.py` | Subtotal, empty cart, total floor, rejected coupons | PRC-01, PRC-02, PRC-06 |
| `tests/test_volume_breaks.py` | Tiers, gift cards | PRC-03, PRC-05 |
| `tests/test_discount_allocation.py` | Per line sums | PRC-04 |

## Must not break
- A cart line never stores a price (PRC-01).
- The total never goes below 0.00 (PRC-02).
- Gift cards never get a volume break (PRC-05).

## Known pitfalls
- Rounding happens only where PRC-03 and PRC-04 say so; do not round the subtotal.

## History
- 2026-03-10: created by trd-create from the seed commit.

# TRD · checkout

Validates a request, computes the totals and builds the receipt. 1:1 map of `src/orders/features/checkout/`.

Rules in the PRD (ID, file in `docs/prd/orders/`): CHK-01..07 ([04](../prd/orders/04-checkout.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry | `checkout`, `Receipt` | CHK-02 |
| `checkout_flow.py` | Validation, subtotal, rounding, totals and the receipt, in one module | `checkout`, `Receipt`, `compute_totals`, `round_cents`, `validate_request`, `render_receipt_text` | CHK-01..07 |

## How it enters the flow
1. `checkout` runs `validate_request` (cart, customer, coupon).
2. `compute_totals` builds the subtotal, asks `pricing.compute_discount` and `shipping.shipping_fee`, and rounds each amount with `round_cents`.
3. `build_receipt` returns the `Receipt`.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_checkout_flow.py` | Totals, rounding, validation errors, receipt text | CHK-01..07 |

## Must not break
- Every amount of the receipt is rounded half up to cents (CHK-01).
- The public API `orders.checkout` and `orders.Receipt` keep their signatures (CHK-02).

## Known pitfalls
- `checkout_flow.py` mixes four responsibilities and is the module to split first.

## History
- 2026-01-05: created by trd-create from the seed commit.

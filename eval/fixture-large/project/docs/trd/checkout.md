# TRD · checkout

Quote, validation, placement and lifecycle of an order. 1:1 map of `src/market/features/checkout/`. May import cart, catalog, pricing, promotions, inventory, payments, shipping, tax. Never imports loyalty: it uses the port.

Rules in the PRD (ID, file in `docs/prd/market/`): CHK-01..10 ([07](../prd/market/07-checkout.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `place_order`, `cancel_order` | CHK-01, CHK-09 |
| `ports.py` | Core to peripheral port for loyalty | `LoyaltyPort`, `set_loyalty_port`, `get_loyalty_port` | CHK-03, CHK-04 |
| `order_models.py` | Dataclasses and status values | `OrderLine`, `OrderQuote`, `Order` | CHK-08 |
| `order_validation.py` | Pre-checks | `validate_checkout` | CHK-05, CHK-07, CHK-10 |
| `order_quote.py` | Order quote: price, loyalty, shipping, tax | `build_quote` | CHK-03, CHK-04 |
| `order_placement.py` | Placement sequence and rollback | `place_order`, `_rollback` | CHK-01, CHK-02, CHK-06 |
| `order_lifecycle.py` | Status moves, cancel, return application | `get_order`, `cancel_order`, `mark_shipped`, `mark_delivered`, `apply_return` | CHK-08, CHK-09 |

## How it enters the flow
1. `api.place_order` calls `order_placement.place_order`; the sequence is in [flow.md](../flow.md).
2. `build_quote` runs `cart_pricing.price_cart`, the loyalty port, `shipping.quote_shipping` and `tax.compute_tax`, in the order of CHK-04.
3. `validate_checkout`, then `inventory.reserve`, `promotion_usage.hold_uses`, the `Order` as `pending`, `payments.charge`.
4. Captured: `inventory.commit`, `commit_uses`, status `paid`, cart converted, event `order.paid`. Failed: `_rollback`.
5. `cancel_order` releases stock and uses, refunds, restocks and publishes `order.cancelled`.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_order_validation.py` | Address, minimum, coupons | CHK-05, CHK-07, CHK-10 |
| `tests/test_order_quote.py` | Totals, loyalty after tax | CHK-03, CHK-04 |
| `tests/test_order_placement.py` | Paid and declined paths | CHK-01, CHK-02, CHK-06 |
| `tests/test_order_lifecycle.py` | Status moves, cancel | CHK-08, CHK-09 |
| `tests/test_ports.py` | Null port | CHK-04 |

## Must not break
- The placement sequence: quote, validate, reserve, hold uses, create, charge, commit or roll back (CHK-02).
- `_rollback` gives back both the stock hold and the coupon uses (CHK-06).
- A decline returns the order as `payment_failed`, it does not raise; the cart stays open (CHK-06).
- An order keeps the prices it was placed with (PRC-01).

## Known pitfalls
- Each placement gets a new order id, so a retry is a new order.
- `cancel_order` and `_rollback` release the same two things; keep them in step.

## History
- 2026-03-10: created by trd-create from the seed commit.

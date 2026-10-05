# TRD · infra

Shared code used by every feature. Map of `src/market/infra/`. Imports no feature.

## Where it lives

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `errors.py` | Exceptions | `MarketError`, `NotFoundError`, `ValidationError`, `OutOfStockError`, `PolicyError` | none |
| `money.py` | Decimal helpers | `D`, `q2`, `pct`, `allocate` | PRC-04 |
| `clock.py` | Injectable clock | `now`, `today`, `set_now`, `advance`, `reset` | CRT-07, INV-04, LOY-05, RET-01 |
| `config.py` | Tunable numbers | `DEFAULTS`, `get`, `set`, `reset` | every `config` rule |
| `events.py` | Event bus | `Event`, `subscribe`, `publish`, `history`, `reset_history` | INV-08, NTF-01..04, LOY-06 |
| `repositories.py` | In-memory repositories | `InMemoryRepository`, `repo`, `reset_all` | none |
| `ids.py` | Id counters | `next_id`, `reset` | none |
| `models.py` | Shared dataclasses | `Product`, `Customer`, `CartLine`, `Cart`, `Address` | CAT-03, SHP-03, TAX-02 |
| `customers.py` | Customer store | `add_customer`, `get_customer` | SHP-03, TAX-01, LOY-02 |

## Events

| Event | Publisher | Payload keys | Subscribers |
|---|---|---|---|
| `inventory.low_stock` | inventory | sku, available | notifications |
| `inventory.restocked` | inventory | sku, available | none |
| `payment.captured` | payments | payment_id, order_id, amount | none |
| `payment.failed` | payments | payment_id, order_id, customer_id, code | notifications |
| `payment.refunded` | payments | payment_id, order_id, amount | none |
| `order.paid` | checkout | order_id, customer_id, points_base, points_redeemed, total | loyalty, notifications |
| `order.cancelled` | checkout | order_id, customer_id, points_base, points_redeemed | loyalty, notifications |
| `return.completed` | returns | return_id, order_id, customer_id, points_base_returned, refund_total | loyalty, notifications |

## Config keys

| Key | Used by |
|---|---|
| `catalog.max_price`, `catalog.max_price_change_percent` | CAT-02, CAT-06 |
| `pricing.volume_tier1_qty`, `_percent`, `pricing.volume_tier2_qty`, `_percent` | PRC-03 |
| `promo.max_total_discount_percent` | PRM-11 |
| `inventory.reservation_minutes`, `inventory.low_stock_threshold` | INV-04, INV-08 |
| `cart.max_lines`, `cart.max_qty`, `cart.ttl_days` | CRT-03, CRT-01, CRT-07 |
| `checkout.min_order_total` | CHK-07 |
| `shipping.free_threshold`, `shipping.free_threshold_vip`, `shipping.max_weight_grams`, `shipping.express_multiplier`, `shipping.surcharge_per_500g` | SHP-03, SHP-06, SHP-05, SHP-02 |
| `payments.max_attempts`, `payments.max_installments`, `payments.min_installment`, `payments.interest_percent_per_extra_installment` | PAY-04, PAY-02 |
| `loyalty.redeem_min_points`, `loyalty.redeem_step`, `loyalty.max_redeem_percent`, `loyalty.expiry_days`, `loyalty.vip_multiplier` | LOY-04, LOY-05, LOY-02 |
| `returns.window_days` | RET-01 |

## Must not break
- Money helpers: `q2` is half up to cents; `allocate` sums exactly to the amount and gives the remainder to the last weight above zero (PRC-04).
- `reset_all` clears repositories, ids, config overrides, clock and event history; subscribers stay.
- Object ids are a prefix (ORD, PAY, RSV, RET, NTF, CRT, REV, ALR), a hyphen and a 4-digit per-prefix counter.
- The fields and defaults of `models.py` are the public data of `market.api`.

## History
- 2026-03-10: created by trd-create from the seed commit.

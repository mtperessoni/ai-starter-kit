# TRD · shipping

Decides the shipping fee from the amount after discounts. 1:1 map of `src/orders/features/shipping/`.

Rules in the PRD (ID, file in `docs/prd/orders/`): SHP-01..02 ([03](../prd/orders/03-shipping.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry | `shipping_fee` | SHP-01, SHP-02 |
| `shipping_fee.py` | Flat fee and the free-shipping threshold | `shipping_fee` | SHP-01, SHP-02 |

## How it enters the flow
1. `checkout_flow.py::compute_totals` calls `shipping_fee` with the subtotal after the rounded discount.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_shipping_fee.py` | Flat fee, below and above the threshold | SHP-01, SHP-02 |

## Must not break
- The fee is a Decimal with two places (SHP-01).

## Known pitfalls
- The threshold compares the amount after discounts, not the subtotal (SHP-02).

## History
- 2026-01-05: created by trd-create from the seed commit.

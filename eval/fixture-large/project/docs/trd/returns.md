# TRD · returns

Eligibility, refund amounts and the return flow. 1:1 map of `src/market/features/returns/`. Peripheral: may import checkout (`order_models`, `order_lifecycle`), payments, inventory, catalog (`category_rules`).

Rules in the PRD (ID, file in `docs/prd/market/`): RET-01..07 ([12](../prd/market/12-returns.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `request_return` | RET-07 |
| `return_models.py` | Dataclasses | `RefundBreakdown`, `ReturnRequest` | RET-03 |
| `return_policy.py` | Eligibility | `REASONS`, `check_eligibility` | RET-01, RET-02, RET-05 |
| `refund_calculator.py` | Amounts | `compute_refund` | RET-03, RET-04 |
| `return_service.py` | The flow | `request_return`, `get_return` | RET-06, RET-07 |

## How it enters the flow
1. `api.request_return` calls `request_return(order_id, items, reason)`.
2. `check_eligibility`, then `compute_refund` (line total after discounts, tax, optional shipping).
3. `payments.refund`, `inventory.add_stock` unless the reason is `defective`, `checkout.order_lifecycle.apply_return`.
4. `return.completed` is published with `points_base_returned` and `refund_total`.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_return_policy.py` | Window, categories, quantities, reasons | RET-01, RET-02, RET-05 |
| `tests/test_refund_calculator.py` | Proration, tax, shipping | RET-03, RET-04 |
| `tests/test_return_service.py` | Refund, stock, status, event | RET-06, RET-07 |

## Must not break
- Refund uses the line total after discounts, not the list price (RET-03, PRC-04).
- Shipping is refunded only on `defective` or `wrong_item` and only when every unit is back (RET-04).
- Defective goods do not go back to stock (RET-06).

## Known pitfalls
- `returned_units` on the order accumulates across returns; RET-05 reads it.

## History
- 2026-03-10: created by trd-create from the seed commit.

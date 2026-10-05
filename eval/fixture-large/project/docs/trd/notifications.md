# TRD · notifications

Emails sent in reaction to events. 1:1 map of `src/market/features/notifications/`. Peripheral: imports no feature (events and `infra.customers` only). Its `__init__.py` calls `register()` once at import.

Rules in the PRD (ID, file in `docs/prd/market/`): NTF-01..05 ([13](../prd/market/13-notifications.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Calls `register()` at import | `register` | NTF-01 |
| `notification_models.py` | Dataclass | `Notification` | NTF-05 |
| `templates.py` | Subjects by template | `TEMPLATES`, `render_subject` | NTF-01..04 |
| `dispatcher.py` | Send once and list | `send`, `list_sent` | NTF-05 |
| `notification_events.py` | One handler per event | `register`, `on_order_paid`, `on_payment_failed`, `on_order_cancelled`, `on_low_stock` | NTF-01..04 |

## How it enters the flow
1. Importing `market.api` imports the package, which subscribes the handlers.
2. `order.paid`, `payment.failed`, `order.cancelled`, `return.completed` and `inventory.low_stock` reach the handlers (see [flow](../flow.md)).
3. A handler resolves the recipient (`infra.customers`, or ops for low stock) and calls `dispatcher.send`.
4. `send` returns `None` when the same template for the same order and recipient was already sent (NTF-05).

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_dispatcher.py` | Send, list, no duplicates | NTF-05 |
| `tests/test_notification_events.py` | Each event to its template | NTF-01..04 |
| `tests/test_templates.py` | Subjects | NTF-01..04 |

## Must not break
- A handler never changes an order or raises into the publisher.
- One email per template, order and recipient (NTF-05).

## Known pitfalls
- Event history is cleared by `reset_all`, but subscribers stay; do not register twice.

## History
- 2026-03-10: created by trd-create from the seed commit.

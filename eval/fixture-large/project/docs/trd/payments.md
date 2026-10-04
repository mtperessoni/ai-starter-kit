# TRD · payments

Charges and refunds through a fake gateway, installments and gift card balances. 1:1 map of `src/market/features/payments/`. Imports no other feature.

Rules in the PRD (ID, file in `docs/prd/market/`): PAY-01..08 ([08](../prd/market/08-payments.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry (re-exports only) | `charge`, `refund` | PAY-01, PAY-07 |
| `payment_models.py` | Dataclasses | `PaymentRequest`, `Payment`, `GatewayResult` | PAY-03 |
| `gateway.py` | Fake gateway by token | `authorize` | PAY-03, PAY-04 |
| `installments.py` | Card plans | `installment_plan` | PAY-02 |
| `gift_cards.py` | Gift card balances | `issue_gift_card`, `gift_card_balance`, `debit_gift_card`, `credit_gift_card` | PAY-05, PAY-07 |
| `payment_service.py` | Charge and refund | `charge`, `refund`, `get_payment` | PAY-01, PAY-03..08 |

## How it enters the flow
1. `order_placement.place_order` calls `charge(order_id, customer_id, amount, request)`.
2. `charge` checks the method and installments, honors the idempotency key, then calls `gateway.authorize` up to the attempt limit.
3. A decline is returned as a failed `Payment` and publishes `payment.failed`; a capture publishes `payment.captured`.
4. `cancel_order` and `returns.return_service.request_return` call `refund`, which publishes `payment.refunded`.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_payment_service.py` | Methods, declines, retries, idempotency, refunds | PAY-01, PAY-03, PAY-04, PAY-06..08 |
| `tests/test_installments.py` | Plans and interest | PAY-02 |
| `tests/test_gift_cards.py` | Balance, debit, credit | PAY-05, PAY-07 |
| `tests/test_gateway.py` | Token behaviors | PAY-03, PAY-04 |

## Must not break
- `charge` never raises on a decline; it raises `ValidationError` only for a bad method or installments (PAY-03).
- The same idempotency key never charges twice (PAY-06).
- Refunds never exceed what was captured (PAY-07).

## Known pitfalls
- The gateway is deterministic by token (`ok_*`, `decline_*`, `fraud_*`, `flaky_N`, `timeout_always`); tests pick behavior with the token.

## History
- 2026-03-10: created by trd-create from the seed commit.

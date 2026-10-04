# features/payments · Payments

Charges and refunds through a fake gateway, installments and gift card balances. Imports no other feature.

- Rules: PAY-01 to PAY-08 in `docs/prd/market/08-payments.md`; index in `docs/prd/INDEX.md`.
- Entry: `charge`, `refund` (`payment_service.py`).
- Collaborators: `gateway` (token driven), `installments`, `gift_cards`, `payment_models`.
- Domain: a decline is a result, not an error; events `payment.captured`, `payment.failed`, `payment.refunded`.

Must not break:
- `charge` never raises on a decline (PAY-03);
- the same idempotency key never charges twice (PAY-06);
- refunds never exceed what was captured (PAY-07).

Tests: `tests/` in this folder.

TRD: `docs/trd/payments.md`

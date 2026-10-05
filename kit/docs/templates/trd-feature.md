# TRD · <area>

<One line: what this area does.> 1:1 map of the area's folder or files, wherever they live.

Rules in the PRD (ID, file in `docs/prd/<prd>/`): PAY-01..12 ([07](../prd/<prd>/07-payment.md)); ORD-04 ([08](../prd/<prd>/08-orders.md)).

## Where it lives

May span several folders; one table per folder.

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `charge_service.py` | Charges a cart with the provider and records the outcome | `ChargeService`, `ChargeOutcome` | PAY-01, PAY-03 |

`domain/` (pure rules):

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `domain/charge_policy.py` | Decides retry or failure from the provider answer | `decide_retry` | PAY-05 |

## How it enters the flow
When wiring is by framework convention, name the convention and the files it binds (AR22).

1. `POST /checkout/pay` (`payment_routes.py::pay`) receives the cart id.
2. `ChargeService.charge` loads the cart and calls the provider through `infra/providers/payment_client.py::PaymentClient`.
3. `decide_retry` reads the answer; on timeout the cart is kept and `PAYMENT_TIMEOUT` is logged.
4. The outcome is stored (`ChargeRepository.save`) and returned.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_charge_service.py` | Success, decline, timeout, retry limit | PAY-01..05 |

Fakes: `FakePaymentClient` (`tests/fakes/payment_client.py`).

## Must not break
- A cart is never charged twice for the same attempt (PAY-04, I-12).
- A timeout keeps the cart (PAY-02).

## Known pitfalls
- Patch `charge_service.PaymentClient`, not `infra.providers.payment_client.PaymentClient`: the patch targets the caller module.

## History
- YYYY-MM-DD: created by trd-create from commit <short>.

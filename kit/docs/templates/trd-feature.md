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

## Planned
Written by prd-flow `writer-trd` for an approved change, removed at promotion. Names only: no parameters, intervals or values (they are rules or contracts, K-51). Contracts live in `changes/NNN-<slug>/design.md`; link it here.

| File | Changes or creates | Symbols | IDs |
|---|---|---|---|
| `charge_service.py` | changes | `ChargeService.charge` | PAY-06 |
| `domain/retry_budget.py` | creates | `RetryBudget` | PAY-06 |

Tests to write (file and IDs only; the expected values are the PRD Example):

| Test file | IDs |
|---|---|
| `tests/test_retry_budget.py` | PAY-06 |

<!-- Delete this section when nothing is planned. No History section: git log is the history (K-55). When this file passes `trd_budget_lines`, split it into docs/trd/<area>/<part>.md plus docs/trd/<area>/README.md. -->

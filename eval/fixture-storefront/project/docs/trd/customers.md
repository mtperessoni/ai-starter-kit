# TRD · customers

Builds the payload the orders service receives from a customer record. 1:1 map of `src/storefront/features/customers/`.

Rules in the PRD (ID, file in `docs/prd/storefront/`): CUS-01..03 ([02](../prd/storefront/02-customers.md)).

## Where it lives

Root:

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `__init__.py` | Public entry | `build_customer_payload`, `CustomerRecord` | CUS-01, CUS-02, CUS-03 |
| `customer_payload.py` | The record type and the payload builder | `CustomerRecord`, `build_customer_payload` | CUS-01, CUS-02, CUS-03 |

## How it enters the flow
1. A storefront page calls `build_customer_payload` with the record and sends the result to the orders service.

## Tests
| File | Covers | IDs |
|---|---|---|
| `tests/test_customer_payload.py` | Fields of the payload, the vip flag, the empty id | CUS-01, CUS-02, CUS-03 |

## Must not break
- The payload holds exactly the fields CUS-01 names.

## Known pitfalls
- The full name of the record never leaves the storefront today (CUS-01).

## History
- 2026-01-05: created by trd-create from the seed commit.

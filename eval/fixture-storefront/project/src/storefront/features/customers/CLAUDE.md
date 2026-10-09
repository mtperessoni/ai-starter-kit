# features/customers · Customers

Builds the payload the orders service receives from a customer record.

- Rules: CUS-01 to CUS-03 in `docs/prd/storefront/02-customers.md`; index in `docs/prd/INDEX.md`.
- Entry: `build_customer_payload` and `CustomerRecord` (`customer_payload.py`), re-exported by `__init__.py`.

Must not break:
- the payload holds exactly the fields CUS-01 names;
- an empty id raises a ValueError (CUS-03).

Tests: `tests/` in this folder.

TRD: `docs/trd/customers.md`

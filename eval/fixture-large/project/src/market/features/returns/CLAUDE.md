# features/returns · Returns

Eligibility, refund amounts and the return flow. Peripheral: may import checkout (`order_models`, `order_lifecycle`), payments, inventory, catalog (`category_rules`).

- Rules: RET-01 to RET-07 in `docs/prd/market/12-returns.md`; index in `docs/prd/INDEX.md`.
- Entry: `request_return` (`return_service.py`).
- Collaborators: `return_policy` (`check_eligibility`), `refund_calculator` (`compute_refund`), `return_models`.
- Domain: refund from the line total after discounts, tax of those units, shipping only when all units are back.

Must not break:
- the refund uses the split line total (RET-03);
- defective goods do not return to stock (RET-06);
- a completed return refunds, lowers the status, takes back points (RET-07).

Tests: `tests/` in this folder.

TRD: `docs/trd/returns.md`

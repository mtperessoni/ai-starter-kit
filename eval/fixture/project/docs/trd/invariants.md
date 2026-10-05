# Invariants · TRD

What a code change must not break, by kind of change. Sources: `AGENTS.md` "Critical constraints", the [constitution](../../.specify/memory/constitution.md) and the structural tests, cited by file name. The full rule is in the source; here, one line. IDs are stable: a new rule goes at the end of its table with the next free number.

## Any change

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-01 | No em dash (U+2014) in code, docs, prompts or commits | AGENTS.md; prd-gate gate G4 |
| I-02 | Zero comments, except the non-obvious and critical why; no comment cites a ticket | AGENTS.md |
| I-03 | Failing test before the implementation | Constitution, test-first principle |
| I-04 | `python -m pytest -q` is green | CI |
| I-05 | The feature's `CLAUDE.md` and TRD change in the same commit as the code they map | `docs/code-structure.md` AR07, AR13 |

## Money

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-06 | Money is `Decimal`, never `float` | Constitution, exact money principle; `test_receipt_amounts_are_decimals` |
| I-07 | Every receipt amount is rounded half up to cents | `test_discount_is_rounded_half_up_to_cents` |

## Public API

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-08 | `from orders import checkout, Cart, CartItem, Customer, Coupon, Receipt` keeps working with the same signatures | `src/orders/features/checkout/tests/test_checkout_flow.py` |

## Tests

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-09 | Tests cite the PRD ID they prove | `docs/code-structure.md` AR06 |
| I-10 | The suite touches no network and no database | Nothing in the code uses either |

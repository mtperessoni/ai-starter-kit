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

## Payload

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-06 | The payload carries only the fields a PRD rule names | Constitution, minimal customer data principle; `test_payload_has_only_id_and_vip` |

## Public API

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-07 | `from storefront import build_customer_payload, CustomerRecord` keeps working with the same signatures | `src/storefront/features/customers/tests/test_customer_payload.py` |

## Tests

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-08 | Tests cite the PRD ID they prove | `docs/code-structure.md` AR06 |
| I-09 | The suite touches no network and no database | Nothing in the code uses either |

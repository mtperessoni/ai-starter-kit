# TRD (F6)

IDs, texts and paths in the examples are illustrative: always read the real line.

The TRD says where each feature lives in the code and what must not break; the rules stay in the PRD and the TRD never repeats them. Before code, it receives the design of the target state, so the plan and the agents start from an approved map and not from the current code.

## "Planned" section
At the end of the feature file (`docs/trd/<feature>.md`, 1:1 with `src/features/<feature>/`, rule AR13), before "History". Proposed paths and names follow `docs/code-structure.md` (feature folder, file named after its responsibility, size limits):

```markdown
## Planned (<name of the change>, <branch>)
Rules: CHK-02, CHK-13 → [04](../prd/product/04-checkout.md)

| File | Changes or creates | Symbols |
|---|---|---|
| `src/features/checkout/payment_config.py` | changes | `PaymentConfig.provider_timeout_seconds` |
| `src/features/checkout/payment_call.py` | changes | `call_provider` |

Entry into the flow: <path by symbols, as in "How it enters the flow">.
Tests to write: `src/features/checkout/tests/test_payment_call.py` (CHK-02: provider silent for 20 s ends with "try again" and the cart kept); ...
Invariants: I-31 (new, <one line>) · affected: I-12.
Must not break: <what of the "Must not break" section the change touches>.
```

Only file and symbol names; never lines or default values. Every cited ID must exist in the PRD (the gate checks).

## Area without a file
Create `docs/trd/<area>.md` with the sections of the existing files (Where it lives, How it enters the flow, Tests, Must not break, Known pitfalls, History), filled with what you verified in the code, and add the row to the table in `docs/trd/README.md`.

## Invariants and tests
- New invariant: next free row of the table for its kind of change in `invariants.md`, with its proof (a test or a principle).
- `testing.md` only if a new target, fake or way of running appears.

## Promotion (last task of the plan)
Merge "Planned" into the body sections, with the names the code actually used, and remove the section.

## Gate and commit
Run the gate and commit `docs(trd): <sentence>`, after the PRD commit, no push.

# TRD (F6)

IDs, texts and paths in the examples are illustrative: always read the real line.

The TRD says where each feature lives in the code and what must not break; the rules stay in the PRD and the TRD never repeats them. Before code, it receives the design of the target state, so the plan and the agents start from an approved map and not from the current code. It is written only after the user confirms the rule diff (C5 step 7).

## "Planned" section
The heading text is `repo.md` `planned_heading` (default `Planned`); the gate reads it from there.

At the end of the area file (`docs/trd/<area>.md`, 1:1 with the area, rule AR13). When the area is split (section "Size and split"), Planned goes to the part file that owns the rules, not to the folder README. Proposed paths and names follow the repository's layout in `docs/code-structure.md`; the paths in the example are illustrative:

```markdown
## Planned (<name of the change>, <branch>)
Rules: CHK-02, CHK-13 → [04](../prd/product/04-checkout.md)

| File | Changes or creates | Symbols | IDs |
|---|---|---|---|
| `src/features/checkout/payment_config.py` | changes | `PaymentConfig.provider_timeout_seconds` | CHK-02 |
| `src/features/checkout/payment_call.py` | changes | `call_provider` | CHK-02, CHK-13 |

Entry into the flow: <path by symbols, as in "How it enters the flow">.

Tests to write:

| Test file | IDs |
|---|---|
| `src/features/checkout/tests/test_payment_call.py` | CHK-02, CHK-13 |

Invariants: I-31 (new, <one line>) · affected: I-12.
Must not break: <what of the "Must not break" section the change touches>.
```

| ID | Rule |
|---|---|
| TP01 | Planned holds files, symbols and IDs only: no parameters, intervals or values (those are rules or contracts) |
| TP02 | "Tests to write" is the test file and the IDs only, never expected values: they are the PRD Example column |
| TP03 | Contracts live only in `design.md`; Planned links to it |
| TP04 | Plan tasks point to the Planned row by file instead of describing it again (`reference/agent-plan.md`) |
| TP05 | Every cited ID must exist in the PRD, and the module will cite the IDs it implements (G25 checks the IDs column against the files) |

## Size and split
| Rule | Detail |
|---|---|
| Budget | A TRD file over `trd_budget_lines` of `repo.md` warns (G26) |
| Split | The area becomes `docs/trd/<area>/<part>.md`, parts mirroring the PRD section groups, plus `docs/trd/<area>/README.md` listing them; `docs/trd/README.md` points to the folder |
| History | The TRD has no "History" section: `git log` is the history. Existing History sections are not appended to |

## Area without a file
Create `docs/trd/<area>.md` with the sections of the existing files (Where it lives, How it enters the flow, Tests, Must not break, Known pitfalls), filled with what you verified in the code, and add the row to the table in `docs/trd/README.md`.

## Invariants and tests
- New invariant: next free row of the table for its kind of change in `invariants.md`, with its proof (a test or a principle).
- `testing.md` only if a new target, fake or way of running appears.

## Promotion (last task of the plan)
Merge "Planned" into the body sections, with the names the code actually used, and remove the section.

## Gate and commit
Run `gate.py --trd` and commit `docs(trd): <sentence>`, after the PRD commit, no push.

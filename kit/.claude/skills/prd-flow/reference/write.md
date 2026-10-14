# Write (rows, TRD, plan, card; the executor and docs read the parts that name them)

Rule as data: the approved rows are written into the PRD file that owns the ID by the executor that implements them, in the same commit as the code and its tests. No docs agent runs for size S or M, and nothing is promoted afterwards. Docs writes only the size L plan (`plan`), a stale PRD (`c4`) and corrections (`adjust`). Examples are illustrative.

## Rows
Run by the executor in the task that implements the rule, from the sheet's "Becomes" column (the exact row text; an answer that chose another option changes the row to that option) and the `Reply` lines of the prompt.
1. Write each approved row into the table that owns the ID (rules below), the contract and transition lines, and the ADR when `## Survey` has `Protected:` (`docs/adr/README.md`; at least two real negative consequences and two considered alternatives; index updated). A new product context: the anatomy of `.claude/skills/prd-create/reference/anatomy.md`, approved rows only.
2. The TRD body ("TRD").
3. `<python> .claude/skills/prd-flow/scripts/gate.py --fix` regenerates the INDEX IDs column before the commit; the INDEX is never edited by hand. CHANGELOG.md is frozen: kept, never appended. A rule's history is `gate.py --history <ID>`, read from git.
4. One commit with the code and tests; its body is the record (`run.md` "Every agent", Commit).

Never write a mechanism (rollback, switch, configuration key, environment variable, table, column, endpoint) that is not in the sheet or a `Reply` line.

| Situation | How it looks |
|---|---|
| New ID | Next free number of the prefix; never renumber or reuse |
| Example | One line `<given> → <expected outcome>` in product language; required for a rule with a number, a branch or a failure path; the sheet's `Example:` lands here |
| Rewritten | Same ID, new text; the old row stays in git, never in a file |
| Superseded or removed | The row is deleted; the commit body's `Decided:` names the ID |
| `Q-`, `R-`, `S-` answered | Append `*Decided on YYYY-MM-DD: <decision>, see <ID>.*`; nothing is deleted |
| Row without ID | Cited by section and number (`04-02 #5`); never invent an ID |
| `pending code` marker already in a PRD | Stays as it is (D4); no new change adds one |

Source names a file (and symbol), never a line or a default value.

| Change | Where |
|---|---|
| Inside one section | In place, in the table that owns the ID |
| Across sections or variants | An amendment section `<prd>/NN-NN-<slug>.md`, with a short `> [!IMPORTANT]` pointer in each affected section |

Contract and transition: what consumers receive, and what happens to requests in flight, existing records and rollout, are sheet decisions. When no approved row states the answer, write one line under the owning table, citing the rules it qualifies; "nothing changes" is written too:
```markdown
Contract: the receipt layout and its fields do not change (CHK-09).
Transition: from now on for every order; no switch, no migration of existing orders (CHK-09).
```

## Docs modes
Prompt `Mode <plan|adjust|c4>`; the executor owns rows and TRD, docs owns the plan.

| Mode | Does |
|---|---|
| `plan` | Size L, or C2, C3, C6 over more than one task (`Route: docs plan`): `decisions.md` from the reply, `brief.md`, `design.md` and `plan.md` ("Change folder", "Plan", "Card"); the rows are not written here: each lands with the code task that implements it, never in a docs-only commit before the code; committed before the baseline |
| `adjust: <words>` | The plan, cards and `decisions.md` the words touch, in place, never reverted and redone; a new commit; rewrites `<state>/diff.md` (the wave table and the non-table changes in plain words, named in `Files:`) |
| `c4` | The `## Survey` divergence: the PRD row in place (the commit body holds the old text), the TRD body only when files, entry points or tests moved; `gate.py --fix`, `gate.py --step prd` (and `--step trd`) once; one commit |

## TRD
The TRD says where each feature lives and what must not break; it names files and symbols and cites rule IDs, never a rule value. Symbols come from `pack.md`. The last code task of each area owns `docs/trd/<area>.md` and updates the body with the names the code used; there is no section for rules not built yet. Before the commit the executor Greps the old value over all of `docs/` and every open `changes/` folder (CHANGELOG.md and `changes/archive` excluded) and fixes every copy in the same commit.

| ID | Rule |
|---|---|
| TP02 | Tests are named by file and IDs, never expected values (they are the Example column) |
| TP03 | Contracts live only in `design.md` (size L); the TRD links to it |
| TP05 | Every cited ID exists in the PRD; the module cites the IDs it implements |
| TP06 | An open TRD-only decision (no PRD or `DEC-` row settles it) goes into the one `sheet-2.md` while unused, no plan before its reply; else a `Q-` row with the recommended default, never a second sheet |
| TP07 | Each card's Contract covers the TRD IDs of its Owns files; each created symbol has a non-test caller owned by a card |

Over `trd_budget_lines` (G26) an area splits into `docs/trd/<area>/<part>.md` plus a README. No History section. A new area file copies the sections of the others and gets a row in `docs/trd/README.md`. A new invariant takes the next free row of its kind in `invariants.md`, with its proof.

## Change folder
Size S and M have none: the sheet, the cards in the state folder and the commit body are the record. Size L: `changes/NNN-<slug>/` (the number the surveyor reserved) with `decisions.md` (template `docs/templates/change-decisions.md`: the `Reply` lines verbatim, then the DEC rows, `sheet.md` "decisions.md"), `plan.md`, and `brief.md` and `design.md` (templates in `docs/templates/`) before the plan. Only a prompt, config or env change: the plan is the publish or deploy task of `repo.md` "Change routing", no folder. A folder that already covers the touched rules gets the new tasks, up to about 60 KB. With `repo.md` "Spec-kit" `kept`, its `spec.md` cites PRD IDs and defines no FR; `tasks.md` is not used.

## Plan
Size L only. `plan.md`: title, `## Constitution check` (`| Principle touched | How the plan honors it, or the justified violation |`, one row per principle touched), then the cards. No orchestration rule is copied into it. Check with `git log --oneline -- <paths>` which dependencies are done. `code` becomes cards; anything owned by another repository becomes a handoff note with the rule rows, outside the plan.

The docs gate prints the waves (`WAVE n: T01, T02`, critical path first, at most 4 per wave) and `CRITICAL PATH`, and errors when two tasks of a wave own one file. Replace `## Plan` of `state.md` with `Plan: <path>`, the `WAVE n:` and `CRITICAL PATH` lines verbatim, each task's model (`sonnet` unless the card gives a reason) and lens, and a last line `Review: once after the last wave`, extended with `and after wave <n>` for each wave whose created interface a later wave builds on.

Cards are area-sized: several files of one area and their tests, about 10 to 30 minutes of work, 12 or fewer per delivery. When the change implements a list (audit findings, acceptance criteria, rule IDs), `plan.md` carries a table with the columns Item, Task, Test, one row per item; an item without a test is a gap before any dispatch.

## Card
A card has at most 25 lines; every field is mandatory. The surveyor writes `<state>/card.md` for C2, C3, C6 and for each area of a size M change (the Contract rows are the sheet's "Becomes" rows of that area); docs writes the cards of a size L plan.
```markdown
### T03 · <verb + result>
Contract: CHK-02
Why: <at most 3 lines: the user's words or the rule's Example that motivates the task>
Owns: src/features/checkout/payment_call.py, src/features/checkout/tests/test_payment_call.py, docs/prd/product/04-checkout.md
Read: docs/trd/checkout.md, src/features/checkout/payment_call.py::call_provider
Reached from: POST /checkout handler `checkout_route` calls `call_provider` | none (a pure refactor creates no symbol)
Depends on: T01 | none
Creates / consumes: creates `PaymentOutcome.retry_after`; consumes `PaymentConfig.provider_timeout_seconds` (T01)
Tests: test_<behavior> in <file>, citing CHK-02, fails before the change
Decisions: DEC-03 | none
Leave: src/features/shipping/fee.py::free_shipping uses `>` at 200.00 | none
Commit: <type>(<scope>): <sentence>
        Rules: CHK-02            (or: Case: none (<reason in at most 8 words>))
Model: sonnet | opus (only for a new safety decision; reason on this line)
Lens: <a reviewer of repo.md "Reviewers"> | none
```
| Rule | Detail |
|---|---|
| Granularity | A task is at least one file and its test. Split only when the pieces run in parallel (disjoint Owns) and each is about 10 tool calls or more; sequential pieces of one area are one task; a one-rule change is one task |
| Affinity | Tasks reading the same large files go to one executor; waves group tasks by TRD area, two tasks of one area are serial or one |
| Interfaces | Shared names go in `Creates / consumes`; a consumer reads the producer's delivery, never its code |
| Reached from | Every created symbol names its caller; the last task of each feature is its wiring task |
| Owns | At most 8 files, a test path and the PRD file that owns each rule among them, plus the tests outside the area the change breaks (`Grep` who imports the changed symbols) |
| Read | Exact paths or `path::symbol`, about 25k tokens: the executor reads nothing else |
| Leave | The pack's out-of-scope divergences in or near the task's files; nobody changes them |

## Fix card
A cold fix (executor `fix`) gets a handoff of at most 10 lines, complete like a card; when the lines do not fit, `Lines:` is the findings file path:
```
Fix: CS-003, CS-005 (or: close failure)
Lines: <the finding or error lines, verbatim>
Owns: <the files named and their tests>
Read: <exact paths or path::symbol>
Rules: CHK-02
```

## Gate
`scripts/gates.sh docs <slug>` once after everything is written, one rerun after a fix (C4: `gate.py --step prd` and `--step trd`). Stdout carries the errors and `warnings: N (see <file>)`; read that file only to decide on a warning. An error blocks the commit. Among the checks: unique IDs, complete rows, cited IDs exist, a changed rule has a test, no em dash added, the INDEX is current, the waves (size L), and the change number on a remote branch (G27, warning). Earlier drift belongs to the base: list it as out of scope, never fix it.

# Plan for agents (read by the docs agent and the surveyor)

IDs, texts and paths in the examples are illustrative: always read the real line.

The plan comes only from the PRD and the TRD already committed: the rule IDs are the contract. The docs agent writes it in `prd-plan` mode (`trd-plan` for a C2 or an adjustment; or `short` for a rule change mid-execution); the surveyor in `light` mode writes a single card to `<state>/card.md` for a one-task C2, a C3 or a C6. Each card is complete for its executor: it never explores.

## Where the plan lives
Folder `changes/NNN-<slug>/` with the next free number (LT01); size from the case line (LT04). The surveyor created the folder with `decisions.md`, the docs agent in `rules` mode filled it, and the docs agent commits it with the PRD; the plan reuses it. Nothing in `changes/archive/` or a legacy `specs/` is read for current behavior (LT07).

| Size | Files in the folder |
|---|---|
| S | None, or only `plan.md` (a one-task change uses `card.md` in the state folder) |
| M | `brief.md` (LT02, template `docs/templates/change-brief.md`) and `plan.md` |
| L | `brief.md`, `design.md` (LT03, template `docs/templates/change-design.md`) and `plan.md` |

| Situation | Where |
|---|---|
| Only prompt, config or env change | The plan is the publish or deploy task (routing below); no folder |
| A change folder already covers the touched rules | Add tasks to its `plan.md`; never append past about 60 KB, start a new folder. No amendment path into a `spec.md` (LT12) |

Compatibility (LT11): a legacy `specs/` stays untouched as history. With `repo.md` "Spec-kit" `kept`, its `spec.md` cites PRD rule IDs and defines no FR, and `tasks.md` is not used: this plan is.

Plan commit: `docs(changes): <sentence>`, no push. After writing, one run: `gate.py --step plan --plan <plan> --change changes/NNN-<slug>` (LT09; it warns G27 when the same change number exists on a remote branch). It prints the waves (`WAVE n: T01, T02`, critical path first, at most 4 per wave) and the `CRITICAL PATH`; it fails when two tasks of one wave share a file in Owns, or a task touches `docs/` or `changes/` without owning it, and warns when two serial tasks of the same area could be one. The docs agent copies the wave table, with each task's model and lens, into `## Plan` of `state.md`, then runs `scripts/gates.sh baseline <slug>` before any code.

Docs fan-out by context: when the surveyor reports `fan-out: yes` (two or more PRD folders or TRD areas, each with more than about 5 rows), docs `prd-plan` returns one `Route: docs context <context>` per context, the chief dispatches them in one message, and each runs in parallel in `context` mode: it writes only its own PRD and TRD section files and does not commit. Then one docs agent in `prd-plan merge` mode does CHANGELOG, INDEX, HTML, the full `gate.py --step prd --rules <approved-rules.md> --applied`, one `docs(prd)` commit, then the TRD and the plan.

Executor affinity by area: waves group tasks by TRD area, and the parallel width comes from independent areas; two tasks of one area are serial or one task.

## Plan header
Order: title, `## Constitution check`, `## Plan execution rules`, tasks.

| Principle touched | How the plan honors it, or the justified violation |
|---|---|
| <III. ...> | <task or decision that honors it> |

One row per principle the change touches (LT05); it replaces spec-kit's Constitution Check and Complexity Tracking. Order of authority while planning: constitution, PRD, TRD, code; the plan governs only the order of work (LT07).

## Routing by Change via
The table is in `repo.md`, "Change routing". `code` always becomes agent tasks in the format below; anything owned by another repository becomes a handoff note with the rule rows, outside this plan.

## Format of a task
A card has at most 25 lines; every field is mandatory, `Read:` above all: the executor reads only what it lists.

```markdown
### T03 · <verb + result>
Contract: CHK-02 (IDs only; the literal row stays in `approved-rules.md` and the pack)
Owns: src/features/checkout/payment_call.py, src/features/checkout/tests/test_payment_call.py
Read: docs/trd/checkout.md (Planned row), src/features/checkout/payment_call.py::call_provider (exact paths or `path::symbol`, about 25k tokens at most)
Depends on: T01 | none
Creates / consumes: creates `PaymentOutcome.retry_after`; consumes `PaymentConfig.provider_timeout_seconds` (T01)
Tests: test_<behavior> in <file>, docstring citing CHK-02, fails before the change; then scripts/gates.sh related <Owns> and scripts/gates.sh lint
Decisions: DEC-03 (the `decisions.md` rows that bind this task, IDs only) | none
Leave: src/features/shipping/fee.py::free_shipping uses `>` at 200.00 (out-of-scope divergence from the pack, left as it is) | none
Commit: <type>(<scope>): <sentence>
        Rules: CHK-02            (or: Case: none (<reason in at most 8 words>))
Model: sonnet | opus (only for a new safety decision; reason on this line)
Lens: <extra specialized reviewer from repo.md "Reviewers"> | none
```

`Lens:` adds a specialized rubric to the wave review; the `prd-flow-reviewer` reviews whatever it says (per wave, or once after the last wave for a serial plan). `Decisions:` lists the DEC rows that constrain the task (a "no new public name", a contract or a transition answer); executor and reviewer read them by ID. `Leave:` copies the out-of-scope divergences of `pack.md` "Divergences" in or near the task's files; executor and reviewer leave them untouched, even when they look wrong.

Commit trailer: a commit that touches the source folders (`ai-kit.json`) carries `Rules: <IDs>` or `Case: none (<reason>)`; the executor commits its own work with it, and `scripts/gates.sh close` checks it.

Deliveries: the executor writes `.claude/prd-flow/state/<slug>/deliveries/<task>.md` (one file per task, never a shared file) with one `Source: <ID>: <path::symbol>` line per approved code rule the task implements (rewritten rules included, never a list or a range); `promote.py` reads them to fill each rule's Source. Rules changed via config, env, prompt, data or a handoff need no `Source:` line, stay planned, are listed in promote's output and close by their own route (repo.md "Change routing"). "Creates / consumes" names the shared symbols: a consumer reads the producer's delivery file, never its code. `gate.py --step plan` checks: every task has Owns (error), Lens and Model (warning), no ID missing from the PRD (error), and the file size (warning above `plan_budget_kb` of `repo.md`).

| Rule | Detail |
|---|---|
| Granularity by the critical path | A task is at least one file and its test. Split only when the pieces run in parallel (disjoint Owns) and each is at least about 10 tool calls of work; sequential pieces of one area are one task; a one-rule change is one task. Each task is an agent with a cold start |
| Context affinity | Tasks that read the same large files go to the same executor, since parallel agents each reread them |
| Interfaces before parallel work | Names shared between tasks are written in `Creates / consumes` and come from the producer's delivery file |
| Owns | Include the tests outside the area the change will break (`Grep` who imports the changed symbols); a task that discovers one midway stops and routes it |
| TRD | The last code task owns `docs/trd/<area>.md` and merges Planned into the body (trd-planned.md) |

## Fix card
A fix goes to `prd-flow-executor` in `fix` mode with a handoff of at most 10 lines that is complete like a card (when the finding lines do not fit, `Lines:` is the path of the findings file the reviewer wrote in the state folder):

```
Fix: CS-003, CS-005 (or: close failure, promote error)
Lines: <the finding or error lines, verbatim>
Owns: <the files named and their tests>
Read: <exact paths or path::symbol>
Rules: CHK-02
```

The reviewer and the recheck build it from their findings (each finding carries its `Owns:`); `executor close` builds it from the failing lines.

## Plan execution rules
The plan header copies these lines under `## Plan execution rules`, so whoever executes does not depend on the skill:
- Review with a ceiling (`.claude/skills/prd-flow/reference/review.md`): at most 5 rounds per delivery; every wave is reviewed (a serial plan once, after the last wave); from round 2 only the previous findings against the fix commit; Critical is fixed, High is fixed when it fits the approved rules, else the user decides; Medium and Low become pending; an open Critical at round 5, or a round that finds more than the previous one, stops the delivery and goes to the user.
- Every agent stops at its ceiling (review.md V08) and returns the handoff for a new agent of the same role.
- Inside a task, only the related tests; the full suite runs once, in `executor close`.
- Any behavior outside the approved rules, safety included, stops the task and routes to the surveyor in `short` mode (R09).
- Each executor commits its own work with the `Rules:` or `Case: none (...)` trailer and writes `deliveries/<task>.md`.
- Per wave: the wave's executors in one message, each on its card's model; `prd-flow-reviewer` on the wave's commits whatever `Lens:` says; a fix through `executor fix`, then `prd-flow-recheck`. After the last wave, `executor close`.

## Promote is not a task
`executor close` runs `promote.py <slug>` after the last wave, commits its result, then runs `scripts/gates.sh close <slug>`. The plan has no Promote task. What promote leaves as a warning (an amendment fold it cannot decide, prd-writing.md P3) and the `design.md` (L) destinations (decisions to `docs/adr/` with `/adr`, data model to the real schema or migration plus the TRD, contracts to the real artifact plus a TRD link, LT03) are the last code task's job when it owns them; otherwise `executor close` routes them to `prd-flow-docs` in `fold` mode.

## Presentation
The docs agent returns the task table (ID, result, owns, depends on, wave, model, lens) for the user's approval. A change the user asks for is one `trd-plan` dispatch with `adjust: <the user's words>`. Each executor receives only its plan path and task ID: the card already is the contract.

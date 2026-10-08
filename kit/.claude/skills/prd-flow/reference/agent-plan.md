# Plan for agents (C5 step 8)

IDs, texts and paths in the examples are illustrative: always read the real line.

The plan comes only from the PRD and the TRD already committed (C5 step 8, after step 7): the rule IDs are the contract. An agent that receives the rule row and the map does not need to rediscover the domain.

## Where the plan lives
Folder `changes/NNN-<slug>/` with the next free number (LT01); size from the case line (LT04). The surveyor created the folder with `decisions.md` at step 2, the main filled it at step 4, and the docs agent commits it at step 5; the plan reuses it. Nothing in `changes/archive/` or a legacy `specs/` is read for current behavior (LT07).

| Size | Files in the folder |
|---|---|
| S | None, or only `plan.md` |
| M | `brief.md` (LT02, template `docs/templates/change-brief.md`) and `plan.md` |
| L | `brief.md`, `design.md` (LT03, template `docs/templates/change-design.md`) and `plan.md` |

| Situation | Where |
|---|---|
| Only prompt, config or env change | The plan is the publish or deploy task (routing below); no folder |
| A change folder already covers the touched rules | Add tasks to its `plan.md`; never append to a plan past about 60 KB, start a new folder (a big file costs on every executor read). No amendment path into a `spec.md` (LT12) |

Compatibility (LT11): a legacy `specs/` stays untouched as history. With `repo.md` "Spec-kit" `kept`, its `spec.md` cites PRD rule IDs and defines no FR, and `tasks.md` is not used: this plan is.

Plan commit: `docs(changes): <sentence>`, no push. After writing, one run: `gate.py --step plan --plan <plan> --change changes/NNN-<slug>` (LT09; it warns G27 when the same change number exists on a remote branch). It also prints the waves (`WAVE n: T01, T02`, critical path first, at most 4 per wave) and the `CRITICAL PATH`; it fails when two tasks of one wave share a file in Owns, or a task touches `docs/` or `changes/` without owning it, and warns when two serial tasks of the same area could be one. The docs agent writes the plan path and that wave table (the `WAVE n:` lines) into `state.md`; the main executes from there (execution.md E04).

Docs fan-out by context: when the surveyor returns `fan-out: yes` (two or more PRD folders or TRD areas, each with more than about 5 rows), one docs agent per context runs in parallel in `C5 context` mode: it writes only its own PRD and TRD section files, runs no `--applied` over the whole approved file and does not commit. Then one docs agent in `plan` mode merges: CHANGELOG, INDEX, HTML, the full `gate.py --step prd --rules <approved-rules.md> --applied`, one `docs(prd)` commit, then the plan. Otherwise one docs agent does everything.

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
A card has at most 25 lines; all fields are mandatory.

```markdown
### T03 · <verb + result>
Contract: CHK-02 (IDs only; the literal row stays in `approved-rules.md` and the pack)
Owns: src/features/checkout/payment_call.py, src/features/checkout/tests/test_payment_call.py
Read: docs/trd/checkout.md (Planned row), src/features/checkout/payment_call.py::call_provider (exact paths or `path::symbol`, about 25k tokens at most)
Depends on: T01
Creates / consumes: creates `PaymentOutcome.retry_after`; consumes `PaymentConfig.provider_timeout_seconds` (T01)
Tests: test_<behavior> in <file>, docstring citing CHK-02, fails before the change; then scripts/gates.sh related <Owns> and scripts/gates.sh lint
Decisions: DEC-03 (the `decisions.md` rows that bind this task, IDs only) | none
Leave: src/features/shipping/fee.py::free_shipping uses `>` at 200.00 (out-of-scope divergence from the pack, left as it is) | none
Commit: <type>(<scope>): <sentence>
        Rules: CHK-02            (or: Case: none (<reason in at most 8 words>))
Model: sonnet | opus (only for a new safety decision; reason on this line)
Lens: <extra specialized reviewer from repo.md "Reviewers"> | none
```

`Lens:` adds a specialized reviewer to the wave review; `none` means no extra one. The wave review by `prd-flow-reviewer` always runs (execution.md E06). `Decisions:` lists the DEC rows of `changes/NNN-<slug>/decisions.md` that constrain the task (a "no new public name", a contract or a transition answer); executor and reviewer read those rows by ID. `Leave:` copies the out-of-scope divergences of `pack.md` "Divergences" that sit in or near the task's files; executor and reviewer leave them untouched, even when they look wrong.

Commit trailer: a commit that touches the source folders (`ai-kit.json`) carries `Rules: <IDs>` or `Case: none (<reason>)`; `scripts/gates.sh trailers [range]` checks it. The executor's proposed message includes the trailer.

The card cites IDs. Its commit and delivery: the executor ends with a `deliveries.md` block whose `Source: <ID>: <path::symbol>` lines (one line per approved code rule the task implements, rewritten rules included, never a list or a range) are what `promote.py` reads to fill each rule's Source; promote requires a `Source:` line only for rules whose Change via is `code`; rules changed via config, env, prompt, data or a handoff stay planned, are listed in promote's output and are closed by their own route (repo.md "Change routing"). The executor reads the literal row from `approved-rules.md` (new rules) or the pack (unchanged rules), never from the card. "Creates / consumes" names the shared symbols: a consumer reads the producer's block in `deliveries.md` (at `.claude/prd-flow/state/<slug>/deliveries.md`), never the producer's code. `gate.py --step plan` checks: every task has Owns (error), Lens and Model (warning), no ID missing from the PRD (error), and the file size (warning above the `plan_budget_kb` of `repo.md`).

| Rule | Detail |
|---|---|
| Granularity by the critical path | A task is at least one file and its test. Split only when the pieces run in parallel (disjoint Owns) and each piece is at least about 10 tool calls of work; sequential pieces of one area are one task; a one-rule change is one task. Each task is an agent with a cold start, so serial tasks that could be one only add time |
| Context affinity | Tasks that read the same large files (a big module, the same area map) go to the same executor, since parallel agents each reread them |
| Interfaces before parallel work | Names shared between tasks are written in `Creates / consumes` and come from the producer's `deliveries.md` block |
| Owns | Include the tests outside the area that the change will break (search who imports the changed symbols); a task that discovers this midway stops and comes back |
| TRD | The last code task owns `docs/trd/<area>.md` and merges Planned into the body (trd-planned.md) |

## Plan execution rules
The plan header copies these lines under `## Plan execution rules`, so whoever executes does not depend on the skill:
- Review with a ceiling (`.claude/skills/prd-flow/reference/review.md`): at most 5 rounds per delivery (every wave is reviewed; a round is counted only when blocking findings go back for a fix); from round 2 only the previous findings; Critical is fixed, High is fixed if it fits the approved rules, else asked, Medium and Low become pending; an open Critical at round 5, or a round that finds more than the previous one, stops the delivery and talks to the user.
- Every agent stops at its ceiling (review.md V08, the single home of the numbers) and reports.
- Inside a task, only the related tests; the full suite runs once, at the end of all tasks.
- Any behavior outside the approved rules, safety included, stops and goes to the short C5 (R09).
- Each commit carries the `Rules:` or `Case: none (...)` trailer.
- Execution follows `.claude/skills/prd-flow/reference/execution.md`: `scripts/gates.sh baseline <slug>` before wave 1, waves from the table in `state.md`, each task through the `prd-flow-executor` with its card on the task's model, a block in `deliveries.md`, a commit per task by the main thread, a `prd-flow-reviewer` review per wave whatever `Lens:` says, and the checkpoint of E01.

## Promote is not a task
The main runs `promote.py <slug>` after the last wave, commits its result, then runs `scripts/gates.sh close <slug>` (execution.md E20). The plan has no Promote task. What the script leaves as a listed warning (an amendment fold it cannot decide, prd-writing.md P3) and the `design.md` (L) destinations (decisions to `docs/adr/` with `/adr`, data model to the real schema or migration plus the TRD, contracts to the real artifact plus a TRD link, LT03) are the last code task's job when it owns them; otherwise they go to a `prd-flow-docs` dispatch in `fold` mode, never to the main.

## Presentation
Show the user the tasks in a table (ID, result, owns, depends on, wave, model, lens) and ask for approval. Adjust until approved. Execution happens when the user asks: each agent receives only its task card, which already is the contract.

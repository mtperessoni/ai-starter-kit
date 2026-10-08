# Plan for agents (F7)

IDs, texts and paths in the examples are illustrative: always read the real line.

The plan comes only from the PRD and the TRD already committed (C5 step 8, after step 7): the rule IDs are the contract. An agent that receives the rule row and the map does not need to rediscover the domain.

## Where the plan lives
Folder `changes/NNN-<slug>/` with the next free number (LT01); size from the case line (LT04). Step 4 of C5 already created the folder with `decisions.md`, which `writer-prd` commits at step 5; the planner reuses it. Nothing in `changes/archive/` or a legacy `specs/` is read for current behavior (LT07).

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

Plan commit: `docs(changes): <sentence>`, no push. After writing, one run: `gate.py --step plan --plan <plan> --change changes/NNN-<slug>` (LT09; it warns G27 when the same change number exists on a remote branch).

## Plan header
Order: title, `## Constitution check`, `## Plan execution rules`, tasks.

| Principle touched | How the plan honors it, or the justified violation |
|---|---|
| <III. ...> | <task or decision that honors it> |

One row per principle the change touches (LT05); it replaces spec-kit's Constitution Check and Complexity Tracking. Order of authority while planning: constitution, PRD, TRD, code; the plan governs only the order of work (LT07).

## Routing by Change via
The table is in `repo.md`, "Change routing". `code` always becomes agent tasks in the format below; anything owned by another repository becomes a handoff note with the rule rows, outside this plan.

## Format of a task
```markdown
### T03 · <verb + result>
Contract (literal):
| CHK-02 | ... | planned | config | Provider silent for 20 s → "try again" shown, cart kept |
TRD: docs/trd/checkout.md, Planned row `src/features/checkout/payment_call.py` (point to the row, do not describe it again)
Owns: src/features/checkout/payment_call.py, src/features/checkout/tests/test_payment_call.py
Does not touch: <files of other parallel tasks>
Test first: test_<behavior> in <file>, docstring citing CHK-02; fails before the change
Commands: scripts/gates.sh related <files in Owns> · scripts/gates.sh lint
Done when: test green, related tests green, lint green, ratchet green
Depends on: T01 · Parallel with: T02
Creates / consumes: creates `PaymentOutcome.retry_after`; consumes `PaymentConfig.provider_timeout_seconds` (T01)
Model: sonnet (config, docs, test adjustment, small contract) | opus (safety decision, agent prompt, big file, serial chain; reason on this line)
Reviewer: <agent from repo.md "Reviewers"> | none
Commit: <type>(<scope>): <sentence>
        Rules: CHK-02            (or: Case: none (<reason in at most 8 words>))
```

Commit trailer: a commit that touches the source folders (`ai-kit.json`) carries `Rules: <IDs>` or `Case: none (<reason>)`; `scripts/gates.sh trailers [range]` checks it. The executor's proposed message includes the trailer.

The literal rule goes only in the task that owns it; the others cite the ID. "Creates / consumes" tells the executor which blocks of `deliveries.md` to read. `gate.py --plan` checks: every task has Owns (error), Reviewer and Model (warning), no ID missing from the PRD (error), and the file size (warning above the `plan_budget_kb` of `repo.md`).

Split work into tasks only when the pieces run in parallel (disjoint "Owns") or a big file needs its own serial chain; otherwise one task per area. Each task is an agent with a cold start of about a minute, so serial tasks that could be one only add time (LS26). Parallel tasks have disjoint "Owns". Order by dependency and mark what runs together. In "Owns", include the tests outside the area the change will break (search who imports the changed symbols); a task that discovers this midway stops and comes back, and each stop costs a resume.

## Plan execution rules
The plan header copies these lines under `## Plan execution rules`, so whoever executes does not depend on the skill:
- Review with a ceiling (`.claude/skills/prd-flow/reference/review.md`): at most 5 rounds per delivery; from round 2 only the previous findings; Critical is fixed, High is fixed if it fits the rule, Medium and Low become pending; an open Critical at round 5, or a round that finds more than the previous one, stops and talks to the user.
- Every agent prompt carries the ceiling of review.md V08 (the single home of the numbers): stop at the ceiling and report.
- Inside a task, only the related tests; the full suite runs once, at the end of all tasks.
- Any behavior outside the approved rules, safety included, stops and goes to the short C5 (R09).
- Each commit carries the `Rules:` or `Case: none (...)` trailer.
- Execution follows `.claude/skills/prd-flow/reference/execution.md`: baseline once, each task through the `executor` with a one-line prompt on the task's model, a block in `deliveries.md`, a commit per task by the main thread, and a plan with more than 6 tasks or a big file executed in a new session.

## Mandatory final task
```markdown
### TNN · Promote
- PRD: old text literally to the CHANGELOG, remove superseded rows and markers, fill the Source, copy the `decisions.md` rows under `Decisions:` (prd-writing.md, "Promotion")
- Fold amendments (prd-writing.md P3)
- HTML, if any: rebuild it (`build_prd_html.py`, or the same hand edit with `html_mode` hand)
- TRD: merge "Planned" into the body (trd-planned.md, "Promotion")
- `design.md` (L): decisions to `docs/adr/` (`/adr`), data model to the real schema or migration plus the TRD, contracts to the real artifact plus a TRD link (LT03)
- Archive: `git mv changes/NNN-<slug> changes/archive/NNN-<slug>` (LT06)
- prd-flow gate green (`gate.py --final` clean when it is the last open change, LT10), full suite and lint green
```

A plan of at most 3 code tasks, with no `design.md` and no amendment file to fold, puts these steps at the end of its last code task instead of a separate task: a separate Promote agent paid a cold start and rereads for a few edits (LS26).

## Presentation
Show the user the tasks in a table (ID, result, owns, depends on, model, reviewer) and ask for approval. Adjust until approved. Execution happens when the user asks: each agent receives only its task, which already is the contract.

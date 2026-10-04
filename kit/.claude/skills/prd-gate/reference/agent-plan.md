# Plan for agents (F7)

IDs, texts and paths in the examples are illustrative: always read the real line.

The plan comes only from the PRD and the TRD already committed: the rule IDs are the contract. An agent that receives the rule row and the map does not need to rediscover the domain.

## Where the plan lives
| Situation | Where |
|---|---|
| The area has an active spec implementing the touched rules | Spec amendment: new FRs at the end of `specs/NNN-*/spec.md` and the new tasks in a file of their own, `specs/NNN-*/plan-<slug>.md`, with one line in the main plan pointing to it. Never append to a plan already past about 60 KB: every executor reads the header and its section, and a big file costs on every read |
| It does not | `specs/NNN-<slug>/plan.md` with the next free number, in the format below |
| Only prompt, config or env change | The plan is the publish or deploy task (routing below); no spec |

Plan commit: `docs(specs): <sentence>`, no push.

## Routing by Change via
The table is in `repo.md`, "Change routing". `code` always becomes agent tasks in the format below; anything owned by another repository becomes a handoff note with the rule rows, outside this plan.

## Format of a task
```markdown
### T03 · <verb + result>
Contract (literal):
| CHK-02 | ... | planned | config |
TRD: docs/trd/checkout.md, section "Known pitfalls"
Owns: src/features/checkout/payment_call.py, src/features/checkout/tests/test_payment_call.py
Does not touch: <files of other parallel tasks>
Test first: test_<behavior> in <file>, docstring citing CHK-02; fails before the change
Commands: scripts/gates.sh related <files in Owns> · scripts/gates.sh lint
Done when: test green, related tests green, lint green, ratchet green
Depends on: T01 · Parallel with: T02
Creates / consumes: creates `PaymentOutcome.retry_after`; consumes `PaymentConfig.provider_timeout_seconds` (T01)
Model: sonnet (config, docs, test adjustment, small contract) | opus (safety decision, agent prompt, big file, serial chain; reason on this line)
Reviewer: <agent from repo.md "Reviewers"> | none
```

The literal rule goes only in the task that owns it; the others cite the ID. "Creates / consumes" tells the executor which blocks of `deliveries.md` to read. `gate.py --plan` checks: every task has Owns (error), Reviewer and Model (warning), no ID missing from the PRD (error), and the file size (warning above the `plan_budget_kb` of `repo.md`).

Parallel tasks have disjoint "Owns". Order by dependency and mark what runs together. In "Owns", include the tests outside the area the change will break (search who imports the changed symbols); a task that discovers this midway stops and comes back, and each stop costs a resume.

## Plan execution rules
The plan header copies these lines under `## Plan execution rules`, so whoever executes does not depend on the skill:
- Review with a ceiling (`.claude/skills/prd-gate/reference/review.md`): at most 5 rounds per delivery; from round 2 only the previous findings; Critical is fixed, High is fixed if it fits the rule, Medium and Low become pending; an open Critical at round 5, or a round that finds more than the previous one, stops and talks to the user.
- Every agent prompt carries the ceiling: stop at about 80 tool calls or 45 minutes and report.
- Inside a task, only the related tests; the full suite runs once, at the end of all tasks.
- A new decision that changes the safety posture goes back to C5 before code.
- Execution follows `.claude/skills/prd-gate/reference/execution.md`: baseline once, each task through the `executor` with a one-line prompt on the task's model, a block in `deliveries.md`, a commit per task by the main thread, and a plan with more than 6 tasks or a big file executed in a new session.

## Mandatory final task
```markdown
### TNN · Promote PRD and TRD
- PRD: old text literally to the CHANGELOG, remove superseded rows and markers, fill the Source (prd-writing.md, "Promotion")
- HTML, if any: the same edit
- TRD: merge "Planned" into the body (trd-planned.md, "Promotion")
- prd-gate gate green, full suite and lint green
```

## Presentation
Show the user the tasks in a table (ID, result, owns, depends on, model, reviewer) and ask for approval. Adjust until approved. Execution happens when the user asks: each agent receives only its task, which already is the contract.

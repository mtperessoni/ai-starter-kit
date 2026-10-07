---
name: prd-flow
description: Mandatory gate for every task that touches product behavior in this repository. Loads the PRD rule (docs/prd) and the TRD map (docs/trd) before acting, checks that the document still matches the code and, when the request changes a rule, shows the current rule, what would change and the trade-offs, asks for confirmation, interviews until the new rule is clear, and only then updates PRD and TRD and plans the work for agents. When the repository has no PRD yet it hands over to /prd-create and /trd-create. Use whenever someone is about to implement, fix, change or ask about a product behavior, picks up a ticket, bug or feature, even without mentioning the PRD. Typical phrases: "change the rule", "it should", "fix this", "why does it do X", "implement the amendment", "adjust the limit", "/prd-flow". Refactors go through here too (TRD only). Not for CI, dependency bumps or formatting.
---

# prd-flow

The PRD is the source of truth for behavior. A rule change goes **PRD, then TRD, then plan, then code**: starting from the code reproduces the defect and loses the decision. Documents age: when document, code and request disagree, ask citing both sides.

Everything specific to this repository (base branch, commands, big files, reviewers, protected rules, extra interview dimensions, sibling repositories) is in `repo.md`. Read it once per session, in the first batch. Prose written by this skill (PRD, TRD, interview, gate output) is in the language of `repo.md` `language` (default English); IDs, code, commits and file names stay English.

## Context economy
Everything that enters here is reread every round.
- Independent reads in one message. Read by ID (`Grep -n`, then `Read` with offset and limit). The human-reading HTML is never read; big files from `repo.md` only by symbol; a sweep of large code goes to an Explore agent with questions.
- Depth by case; a query does not hunt divergences. An out-of-scope divergence is noted, never investigated.
- Heavy work goes to the workers, which write to `.claude/prd-flow/state/<slug>/`. This conversation classifies, confronts, interviews, approves, dispatches and commits; it does not reopen their files.
- Count and list with the Grep tool (shell proxies can swallow output); patches with `git --no-pager diff`.
- Budgets: context to the user at most 6 lines; confrontation at most 40; round message at most 25; at most 4 questions per round in one AskUserQuestion; worker return at most 30 lines (executor and reviewer at most 20).

## Cases
| Case | When | Route |
|---|---|---|
| C0 no PRD | `docs/prd/INDEX.md` does not exist, or a new product or module needs its own PRD | Stop and run `/prd-create`, then `/trd-create`; come back for the original request |
| C1 query | How something works or why; also "diagnose", "plan" until the user asks for a change | Light route, answer with IDs and Source |
| C2 implement | Approved rule the code does not meet, including committed code that is not wired | Light route + F2, plan (F7), execution |
| C3 bug | Code diverges and the user confirms the PRD is right | Light route + F2, fix |
| C4 stale PRD | Code right, PRD wrong, confirmed | Light route + F2, `writer` without interview |
| C5 rule change | Changed or new rule, gap, or a defect the PRD documents as current behavior | C5 route |
| C6 refactor | Structure changes, behavior does not | Light route with TRD and invariants |

Phases cited in the references: F1 context, F2 PRD versus code check, F5 PRD and F6 TRD (step 5), F7 plan (step 7). State the case and its size (S, M or L, `reference/classification.md`, LT04) in one line; a request with several items has one case per item. Classification traps and the divergence format: `reference/classification.md`, only when in doubt. If C2, C3 or C6 turns out to need different behavior, re-enter as C5.

## Light route (C1, C2, C3, C4, C6)
1. **Batch A:** `Read repo.md` (first time in the session); `Grep` the term or ID in `docs/prd/INDEX.md`; `Read docs/trd/README.md`; `git fetch -q && git rev-list --count HEAD..origin/<base_branch>`.
2. **Batch B:** the tables of the IDs, the area's map (`CLAUDE.md` of its feature folder, or of the map folders its TRD lists) and its TRD (`docs/trd/<area>.md`); with code, the lines of `docs/trd/invariants.md` it cites.
3. **F2 (C2, C3, C4):** the Source exists, does what the rule says and **has a caller outside the tests** (`Grep` the symbol in the source folder). Divergence: side by side, and ask which is right.
4. Answer. Branch behind: `git diff --stat HEAD..origin/<base_branch> -- <paths read>`; pull only if it touches the scope.
5. With code (C2, C3, C6): after the user's confirmation (R01), follow `reference/execution.md`.

## C5 route
| Step | Who | Does | Leaves |
|---|---|---|---|
| 1 | this conversation | Slug, case and approver (`git config user.name`) in `state.md`; `scripts/gates.sh context <slug>` names the run for telemetry | state |
| 2 | `surveyor` | Context, freshness, impact (K01..K10), pre-interview | `pack.md`, `impact.md`, confrontation |
| 3 | this conversation | Confrontation and question: **This is the change I want** · **Do not touch this rule** (C2/C3) · **Adjust the request** (back to 2) | decision |
| 4 | this conversation | Interview (`reference/interview.md`) of what is still open | `interview.md`, `approved-rules.md` |
| 5 | `writer` | PRD, HTML, CHANGELOG, INDEX, gate, `docs(prd)`; TRD "Planned", gate, `docs(trd)` | `writing.md` |
| 6 | this conversation | Only `git diff -U0` of the rule lines | confirmation |
| 7 | `planner` | Size M and L: `brief.md` (and `design.md` for L); `plan.md` in `changes/NNN-<slug>/` with one contract per task; `gate.py --plan` and `--change <dir>` without errors | task table |
| 8 | this conversation | Plan approval. More than 6 tasks or a big file: execute in a new session | end of the docs phase |
| 9 | `executor`, `reviewer` | `reference/execution.md`: baseline, waves, commit per task, review with ceiling, short C5 if a rule changes | delivery, `deliveries.md` |

Worker: Agent `general-purpose`, `model: "sonnet"` (the executor on the task's model), prompt *"Read `.claude/skills/prd-flow/reference/workers.md`, section `<name>`, and run it for slug `<slug>`. Request: <one line>."* The reviewer is the agent `repo.md` names for the task, with the `reviewer` section. Never copy briefings into the prompt. A gap in a return is resolved before the next step. Without the Agent tool, run the section here with the same briefing and budget.

## State
`.claude/prd-flow/state/<slug>/` (outside git): `state.md` (case, phase, base, decisions, `review: N/5` counter, cost per wave), `pack.md`, `impact.md`, `interview.md`, `approved-rules.md`, `writing.md`, `baseline-failures.txt`, `deliveries.md`. Intent, plan and tasks live in `changes/NNN-<slug>/` (LT01), never truth: at the end the Promote task moves what is durable to its home and archives the folder (LT06). Authority: constitution, PRD, TRD, code; `changes/archive/` and a legacy `specs/` are never read for current behavior (LT07). Resume (`/prd-flow resume <slug>`): only `state.md` and the current phase file; with `git diff --quiet <base> origin/<base_branch> -- <pack paths>`, the pack is still valid.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, the source folder or tests before its time: C5 from step 5 on; C2, C3, C4 and C6 after the user confirms the case. A requested diagnosis is only a diagnosis |
| R02 | Code and PRD answer the facts; the user answers the intent |
| R03 | Prose is in the `repo.md` `language` (default English); IDs, code, commit messages and file names are always English. No em dash (U+2014) in docs, code or commits. Push and PR only on the user's explicit request |
| R04 | The interview runs here: a worker never talks to the user |
| R05 | Code review: at most 5 rounds per delivery; an open Critical at round 5 stops everything and goes to the user (`reference/review.md`) |
| R06 | Every agent has a ceiling and returns what is missing; none is re-dispatched in a loop (review.md V08) |
| R07 | Questions to the user in product language, with a usage example; IDs only in the read-back |
| R08 | Code and TRD follow `docs/code-structure.md` (AR01 to AR28): the right area per the repository's layout, the size limits, one responsibility per file, composition, the PRD ID in the first comment of each module and test, the area's map and TRD updated in the same commit. The ratchet (command in `repo.md`) never regresses |

## Files
| File | Who reads it |
|---|---|
| `repo.md` | this conversation, once per session; workers when their section says so |
| `reference/classification.md` | this conversation, when in doubt about the case, a divergence or a real session to explain |
| `reference/interview.md` | this conversation, at step 4 |
| `reference/execution.md`, `reference/review.md` | whoever executes and reviews (step 9 and light route with code); the planner for the plan execution rules |
| `reference/workers.md` | each worker, only its own section |
| `reference/impact.md`, `prd-writing.md`, `trd-planned.md`, `agent-plan.md` | workers only |
| `scripts/gate.py` | run only: `python .claude/skills/prd-flow/scripts/gate.py [--base REF] [--pack F] [--rules F] [--plan F] [--change DIR] [--trace] [--final]` |

## Final
Case, IDs touched, commits, plan path and out-of-scope divergences. With code: the findings of `scripts/gates.sh retro`, or one line saying the run stayed within every threshold (E20).

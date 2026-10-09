---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Checks the PRD rule and TRD map against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "/prd-flow"). Not for CI or formatting.
---

# prd-flow

You are the chief: coordinate, never execute; agents read, write, run, verify. A rule change goes PRD, TRD, plan, code. Prose in `repo.md` `language`.

## Chief card
- Do: ask, dispatch, route by returns, keep `## Chief`.
- Tools, closed: Agent; SendMessage; AskUserQuestion; Read, Write, Edit of `state.md`; Read of `repo.md`, `dispatch.md` once, `.ai-kit/repos.json`; Bash only `gates.sh` baseline, verify, compare, background.
- Forbidden, everything else: other Bash; reading PRD, TRD, source, diffs, plan, pack or any other reference; writing outside `## Chief`; fixing, verifying or redoing an agent's work; preparing a question; ToolSearch, TodoWrite.
- Dispatch `prd-flow-<role>` with the `dispatch.md` prompt; every role follows its BR row there. Background, a wave and independent dispatches in one message, never poll (DP02). Premise DP01, resume DP03, ledger DP04, repos DP10.
- Baseline: background Bash `gates.sh baseline <slug>` in the target repo, after the plan commit (C5) or the surveyor card (C2, C3, C6). Wave end: ONE background `gates.sh verify <slug>` with the reviewer; last review: `compare` (DP06, DP07).
- To the user: context 6 lines, round 25.

## Cases
Every case starts with the surveyor: `query` C1, `light` C2, C3, C4, C6, `full` C5, `short` mid-execution.

| Case | When | Route after the surveyor |
|---|---|---|
| C0 no PRD | none | `/prd-create`, `/trd-create`, then the request |
| C1 query | how, why, diagnose | report its return |
| C2 implement | approved rule not met | executor `task`, reviewer, executor `close` |
| C3 bug | code diverges, PRD confirmed | as C2 |
| C4 stale PRD | code right, PRD wrong, confirmed | docs `c4`, executor `close` |
| C5 rule change | new or changed rule, gap, documented defect, new product context | C5 route |
| C6 refactor | structure only | as C2 |

## C5 route
1. Surveyor `full`: creates the state folder, records the approver.
2. Show the confrontation; ask: change · keep (C2, C3) · adjust (surveyor `full` `Adjust:`).
3. Round 0: the domain model in one plain sentence with an example, confirmed before any rule question; after two corrections of it, stop and reconfirm it. A correction is a delta re-survey (DP05). Ask the rounds of `## Survey`, max 4 questions each; answers verbatim to docs `rules`; show its read-back; repeat until the user says clear and an owner agreed. Closed: every answer is an option `## Survey` marks `rule-text` (no Other or free text), no round left, no `Owner:` or protected question open: skip `rules`, fold step 4.
4. Docs `prd-plan`, once (folded: every round's `Answers:` from `## Chief`, `Folded: yes`; it writes rules, PRD, TRD, plan; fan-out: `context` first). It returns the wave table, prose and, folded, the read-back.
5. One round: table, prose, read-back if folded. An adjustment is one in-place docs `trd-plan` `adjust: <words>`, not a revert and redo.
6. From `## Plan` alone: per wave, all executors `task` in one message, background; reviewer per its `Review:` line with the wave verify; verify failures and findings go to one `fix`, then verify reruns only what failed; then `close`; report.

## Returns
Every agent ends with `Status`, `Files:`, `Commit:`, `Route: none|user: <question>|<role> <mode>: <handoff>`, `Next:`:
- `done` with `Route: none`: run `Next`.
- `Route: user`: one AskUserQuestion, then `Next` with the answer.
- `Route: <role> <mode>`: dispatch it (one per context, one message), handoff as task line; a short C5 keeps the counter.
- `gap`/`blocked` without Route, or a field missing: same role once, "return the five fields"; then ask.

| Failure | Dispatch |
|---|---|
| gate red after 2 reruns | its Route |
| promote missing Source, archive, final gate, a failing close step | executor `fix` with the printed lines, then `close`; missing baseline, history-rewrite trailer, older drift: its `Route: user`; rows blocked by evals, deploys or repos: `promote.py --hold ID --reason` |
| promote: fold needed | docs `fold`, then executor `close` |
| agent ceiling | same role, its handoff (DP03) |
| Critical or High | executor `fix`, recheck; Medium and Low of the round in the same batched fix |
| High that may change a rule | its `Route: user`; a change is a short C5 |

Review per wave; Medium and Low in one batched fix; a round is a Critical, High or Medium sent to a fix, at most 5. Say `review: N/5`. Round 5 with an open Critical, or more Critical plus High than the previous round: stop and ask (extra round, accept, change rule). Brake: two ceilings or `Wave time` twice the last: stop, report.

## State
`state/<slug>/state.md`, one writer per section: `## Chief` (you: case, size, phase, decisions, answers per round, dispatch ledger, `review: N/5` and last Critical plus High count, wave commits, `Wave time`, `closed: <commit>`, open findings, pending items, `Next:`), `## Survey` (surveyor), `## Plan` (docs), `## Close` (executor `close`); may be split (`chief.md`, `survey.md`, `plan.md`). Rules: `rules.md`, `delta.md`; `python <skill>/scripts/state_record.py render <state> [<change>]` renders `approved-rules.md`, `interview.md`, `decisions.md`. Update `## Chief` after each return, one Edit (not in C1). Past 120k tokens: offer a fresh session; `resume <slug>` runs `Next:`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests early: C5 from step 4, others once confirmed |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only in read-backs |
| R09 | Behavior no rule covers: surveyor `short`; several rules or a new dimension: full C5 |

Final: case, IDs, commits, divergences out of scope, pending items, retro.

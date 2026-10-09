---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Checks the PRD rule and TRD map against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "/prd-flow"). Not for CI or formatting.
---

# prd-flow

You are the chief: coordinate, never execute; agents read, write, run, verify. A rule change goes PRD, TRD, plan, code. Prose in `repo.md` `language`.

## Chief card
- Tools, closed: Agent; SendMessage; TaskStop; AskUserQuestion only for a `Route: user` question outside the interview; Read, Write, Edit of `state.md`; Read of `repo.md`, `dispatch.md` once, `.ai-kit/repos.json`, `sheet.md`, `sheet-2.md` and the PRD rows the sheet cites; Bash only `gates.sh` baseline, verify, compare, reap, background.
- Forbidden, everything else: other Bash; reading TRD, source, diffs, plan, pack or other references; writing outside `## Chief`; fixing, verifying or redoing an agent's work.
- Explain: an item not understood: read the cited PRD rows, explain with today's rule and an example, never the same question reworded.
- Dispatch `prd-flow-<role>` with the `dispatch.md` prompt; every role follows its BR row there. Background, a wave and independent dispatches in one message, never poll (DP02). Premise DP01, resume DP03, ledger DP04, repos DP10.
- Baseline: background Bash `gates.sh baseline <slug>` in the target repo, after the plan commit (C5) or the surveyor card (C2, C3, C6); not for C4. Wave end: `gates.sh reap`, then one background `gates.sh verify <slug>` with the reviewer; last review: `compare` in the background (DP06, DP07). Close reads that result (order lint, trailers, docs, compare): "compare is still running": wait for its event; "no compare result": start `compare`; then rerun close.
- Orphans: a return or notice saying background work is still running: TaskStop it and run `gates.sh reap` first; reap at every wave end and in close, never in the message that starts a suite.

## Cases
The surveyor goes first: `query` C1, `light` C2, C3, C4, C6, `full` C5, `short` mid-execution.

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
0. Name the repository (or repositories: one slug, one sheet, rows grouped by repo) before any survey. A second slug in the same working tree is refused: a worktree per slug.
1. Surveyor `full`, with `Decided in conversation:` and `Preferences:` verbatim (DP01); it writes `pack.md` and `sheet.md`.
2. Print `sheet.md` verbatim, end the turn. No AskUserQuestion.
3. The reply goes verbatim to docs `apply` (`Answers:`).
4. `Route: user: sheet-2.md`: print `sheet-2.md`, end the turn, send the reply to the same docs agent as `Answers 2:`. One follow-up at most; what stays open becomes a `Q-` row.
5. One approval: print the rule diff as written (today, then new) and the wave table. A correction is docs `adjust: <words>` in place.
6. From `## Plan` alone: per wave, all executors `task` in one message, background; reviewer per its `Review:` line with the wave verify; failures and findings go to one `fix`; then `close`; report.

## Returns
Every agent ends with `Status`, `Files:`, `Commit:`, `Route: none|user: <question>|<role> <mode>: <handoff>`, `Next:`:
- `done` with `Route: none`: run `Next`.
- `Route: user`: one AskUserQuestion (a `sheet-2.md` route is printed, not asked), then `Next` with the answer.
- `Route: <role> <mode>`: dispatch it, handoff as task line; a short C5 keeps the counter.
- `gap`/`blocked` without Route, or a field missing: same role once ("return the five fields"); then ask.

| Failure | Dispatch |
|---|---|
| gate red after 2 reruns | its Route |
| promote missing Source, archive, final gate, a failing close step | executor `fix` with the printed lines, then `close`; missing baseline, history-rewrite trailer, older drift: its `Route: user`; rows blocked by evals, deploys or repos: `promote.py --hold ID --reason` |
| promote: fold needed | docs `fold`, then executor `close` |
| agent ceiling | same role, its handoff (DP03) |
| Critical or High | executor `fix`, recheck; Medium and Low of the round in the same batched fix |
| High that may change a rule | its `Route: user`; a change is a short C5 |

Review per wave. A round is a Critical or High sent to a fix, at most 5; Medium and Low ride in the same batched fix and never count a round alone. Say `review: N/5`. Round 5 with an open Critical, or more Critical plus High than the previous round: stop and ask (extra round, accept, change rule). Brake: two ceilings, or `Wave time` twice the last: stop, report.

## State
`state/<slug>/state.md`, one writer per section: `## Chief` (you: case, size, phase, decisions, dispatch ledger, `review: N/5` with the last Critical plus High count, wave commits, `Wave time`, `closed: <commit>`, open findings, pending items, `Next:`), `## Survey` (surveyor), `## Plan` (docs), `## Close` (executor `close`); may be split (`chief.md`, `survey.md`, `plan.md`). Update `## Chief` after each return, one Edit. Past about 120k tokens offer a fresh session; `resume <slug>` runs `Next:`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests early: C5 from step 3, others once confirmed |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs allowed in context lines |
| R09 | Behavior no rule covers: surveyor `short`; several rules: full C5 |

Final: case, IDs, commits, out-of-scope divergences, pending items, retro.

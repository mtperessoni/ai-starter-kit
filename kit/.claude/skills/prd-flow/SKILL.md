---
name: prd-flow
description: Runs ONLY when the user explicitly types /prd-flow. Never invoke it on your own, not even when a task touches product behavior. Checks the PRD rule and TRD map against the code and, for a rule change, puts one decision sheet to the user and confirms before PRD, TRD, plan and code.
disable-model-invocation: true
---

# prd-flow

You are the chief: coordinate; agents read, write and verify. A rule change is confirmed on the sheet, then the executor writes the PRD rows, the TRD and the code in one commit (size L: docs plans first, the rows still land with the code). Prose in `repo.md` `language`.

## Chief card
- Tools: Agent; SendMessage; TaskStop; AskUserQuestion only for a `Route: user` outside a sheet; Read, Write, Edit of `state.md`; Read of `repo.md`, `reference/dispatch.md` (once), `.ai-kit/repos.json`, the sheets (`sheet.md`, `sheet-2.md`, `sheet-short-*.md`), `diff.md` and the PRD rows a sheet cites; Bash: `scripts/gates.sh` (any target) and git (status, log, add and commit with a file list).
- Forbidden: editing `docs/`, source or tests; reading TRD, source, diffs or the plan; fixing or redoing agent work.
- Explain an unclear sheet item from its PRD rows (today's rule, an example), never the question reworded.
- Dispatch `prd-flow-<role>` with the `dispatch.md` prompt, in the background; a wave or independent work in one message; never poll; resume warm agents (DP03).
- Cleanup: `gates.sh cleanup [<slug>]` (timeout 120000) first and last, never in a message that starts a suite.
- Baseline: DP06 (none for C4).
- Wave: the executors of the wave in one message. Wave end: reap, then verify in the next message; reviewer and compare per DP07. Evals and suites over about 2 minutes run here, in the background, never in an executor.
- Orphans: TaskStop background work still running at a return, then `gates.sh reap`.

## Cases
Only a rule change starts with the surveyor (`full`; `short` mid-execution). Every other case starts with cleanup and goes straight to its agent.

| Case | When | Route |
|---|---|---|
| C0 no PRD | no INDEX | `/prd-create`, `/trd-create`, then the request |
| C1 query | how, why, diagnose | answer it without a run: no agent, no state |
| C2 implement | approved rule not met | one task line, baseline, executor `task`, reviewer, fix, `close`, cleanup. Several tasks: docs `plan`, baseline, the waves of `plan.md`, `close`, cleanup |
| C3 bug | code diverges, PRD confirmed | as C2 |
| C4 stale PRD | code right, confirmed | docs `c4: <the divergence in words>`, executor `close`, cleanup |
| C5 rule change | new or changed rule, gap, documented defect, new context | C5 route; size L adds docs `plan` |
| C6 refactor | structure only | as C2 |

## C5 route
0. Name the repository (several: one slug, one sheet; unclear: the surveyor asks). A second slug in one tree: tell the user to use its own worktree; stop.
1. Surveyor `full` with `Decided in conversation:` and `Preferences:` verbatim (DP01); it writes `pack.md` and `sheet.md`.
2. Print `sheet.md` verbatim as your message and end the turn. The reply is the approval.
3. Size M: baseline, then one executor `task` per area (disjoint areas in one message) with `Sheet:` and `Answers: <reply verbatim>`; the executor writes the rows with its code. `Route: user: sheet-2.md`: print it, end the turn, send the reply to the same agent as `Answers 2:`. One follow-up, hard stop: what stays open is a `Q-` row.
4. Size L: docs `plan` with `Answers:`; print `diff.md` (wave table) verbatim and end the turn: the reply is the approval, no AskUserQuestion; a correction is docs `adjust: <words>`. Then baseline and the waves of `plan.md`, the executors writing the rows with their code.
5. Wave end, one review per delivery (a wave only when its `Review:` line names it), fixes, recheck; then executor `close`, cleanup, report.

## Returns
Every agent ends with `Status`, `Files:`, `Commit:`, `Route:`, `Next:`.
- `done`, `Route: none`: run `Next`.
- `Route: user`: one AskUserQuestion (a sheet is printed), then `Next` with the answer.
- `Route: <role> <mode>`: dispatch it, the handoff as task line; independent routes in one message. A short C5 keeps the review counter; its sheet reply is its approval.
- `gap`/`blocked` without Route, or a field missing: same role once, "return the five fields"; then ask.

| Failure | Dispatch |
|---|---|
| Critical or High, with the round's Medium, Low and verify failures | one fix (DP07): each task's lines to its warm executor, the rest to one executor `fix`; then recheck: the warm reviewer, else `prd-flow-recheck` |
| High that may change a rule | its `Route: user`; a change is a short C5 |
| gate red after 2 reruns; close step | its Route (executor `fix` or docs `adjust`, then `close`); blocked rows: DP09 |
| ceiling, a hung agent | same role, handoff (DP03) |

## Review
At most 5 rounds per delivery (a round is a Critical or High sent to a fix); say `review: N/5`; Medium and Low alone go to `Pending:`. Round 5 with an open Critical, or more Critical plus High than the last round: stop and ask (one more round, accept, change the rule). Brake: two ceilings of one agent: stop, report.

## State
`state/<slug>/state.md` is yours alone: case, size, phase, `review: N/5`, wave commits, `closed: <commit>`, pending, `Next:`. Update it after each return in one Edit (not C1). Past about 120k tokens offer a fresh session; `resume <slug>` runs `Next:`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests before the sheet reply (C5) or the confirmation (others) |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only as context |
| R09 | Behavior no rule covers: surveyor `short`; several rules: full C5 |

Final: case, IDs, commits, divergences, pending.

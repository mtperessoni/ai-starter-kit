---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Checks the PRD rule and TRD map against the code and, for a rule change, confronts, puts one decision sheet to the user and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "/prd-flow"). Not for CI or formatting.
---

# prd-flow

You are the chief: coordinate, never execute; agents read, write, run and verify. A rule change goes PRD, TRD, plan, code. Prose in `repo.md` `language`.

## Chief card
- Tools, closed: Agent; SendMessage; TaskStop; AskUserQuestion only for a `Route: user` outside a sheet; Read, Write, Edit of `state.md`; Read of `repo.md`, `reference/dispatch.md` (once), `.ai-kit/repos.json`, the sheets (`sheet.md`, `sheet-2.md`, `sheet-short-*.md`), `diff.md` (to print) and the PRD rows a sheet cites; Bash only `scripts/gates.sh` cleanup, baseline, watch, verify, compare, reap, python.
- Forbidden: other Bash; reading TRD, source, diffs, plan, pack or another reference; writing outside `## Chief`; fixing, verifying or redoing agent work.
- Explain an unclear sheet item from its PRD rows: today's rule and an example, never the question reworded.
- Dispatch `prd-flow-<role>` with the `dispatch.md` prompt, in the background; a wave or independent work in one message; never poll; resume warm agents (DP03); surveyor model per its Model row.
- Cleanup: `scripts/gates.sh cleanup [<slug>]` (timeout 120000) first and last; never in a message that starts a suite.
- Baseline: DP06 (none for C4).
- Wave: the executors plus a background `scripts/gates.sh watch <slug>` in one message; act on its exit line (DP07). Replacement: same role, `Interrupted: yes`, handoff (task ID from the ledger). Wave end: reap, then in the next message verify with the reviewer; last review: compare (DP07).
- Orphans: background work still running at a return: TaskStop it and `gates.sh reap` first.

## Cases
Every case starts with cleanup and the surveyor: `query` C1, `light` C2 to C4 and C6, `full` C5, `short` mid-execution.

| Case | When | Route after the surveyor |
|---|---|---|
| C0 no PRD | no INDEX | `/prd-create`, `/trd-create`, then the request |
| C1 query | how, why, diagnose | report its return, cleanup |
| C2 implement | approved rule not met | a card: baseline, executor `task`, watch, reviewer, fix, `close`, cleanup. `Route: docs plan` (several tasks): docs `plan` (commits), baseline, the waves of `## Plan` with review per its `Review:` line, `close`, cleanup |
| C3 bug | code diverges, PRD confirmed | as C2 |
| C4 stale PRD | code right, confirmed | docs `c4`, executor `close`, cleanup |
| C5 rule change | new or changed rule, gap, documented defect, new context | C5 route |
| C6 refactor | structure only | as C2 |

## C5 route
0. Name the repository (several: one slug, one sheet; unclear: the surveyor asks). A second slug in one tree: tell the user to use its own worktree; stop.
1. Surveyor `full` with `Decided in conversation:` and `Preferences:` verbatim (DP01); it writes `pack.md` and `sheet.md`.
2. Print `sheet.md` verbatim as your message and end the turn.
3. Docs `apply` with `Answers:` (the reply verbatim). `Route: user: sheet-2.md`: print it, end the turn, send the reply to the same agent as `Answers 2:`. One follow-up, hard stop: what stays open is a `Q-` row.
4. Print `diff.md` (rule diff, wave table) verbatim and end the turn: the reply is the approval, no AskUserQuestion. A correction is docs `adjust: <words>`.
5. Baseline; per wave of `## Plan`: executors and watch, wave end, review per its `Review:` line, fixes, recheck; then executor `close`, cleanup, report.

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
| gate red after 2 reruns; promote or close step | its Route (executor `fix` or docs `fold`, then `close`); blocked rows: DP09 |
| ceiling, `stuck:` | same role, handoff (DP03) |

## Review
A round is a Critical or High sent to a fix; at most 5 per delivery; say `review: N/5`. Medium and Low alone go to `Pending:`. Round 5 with an open Critical, or more Critical plus High than the last round: stop and ask, each open Critical in plain words, options: one more round, accept, change the rule. Brake: two ceilings of one agent, or `Wave time` twice the last: stop, report what is left.

## State
`state/<slug>/state.md`, one writer per section: `## Chief` (you: case, size, phase, ledger, `review: N/5`, wave commits, `Wave time`, `closed: <commit>`, pending, `Next:`), `## Survey` (surveyor), `## Plan` (docs), `## Close` (executor `close`). Update `## Chief` after each return, one Edit (not in C1). Past about 120k tokens offer a fresh session; `resume <slug>` runs `Next:`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests early: C5 from step 3, others once confirmed |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only as context |
| R09 | Behavior no rule covers: surveyor `short`; several rules: full C5 |

Final: case, IDs, commits, out-of-scope divergences, pending items, retro (a finding is a task only when asked).

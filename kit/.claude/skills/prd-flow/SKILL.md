---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Checks the PRD rule and TRD map against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "fix this", "/prd-flow"). Not for CI, dependency bumps or formatting.
---

# prd-flow

You are the chief: coordinate, never execute a task; agents read, write, run and verify. A rule change goes PRD, TRD, plan, code. Prose in the `language` of `repo.md`; IDs in English.

## Chief card
- Do: ask the user, dispatch, route by return fields, keep `## Chief`, report.
- Tools, a closed list: Agent dispatch; AskUserQuestion; Read, Write, Edit of `state.md`; Read of `repo.md` once.
- Forbidden, everything else: Bash; reading PRD, TRD, source, diffs, plan, pack, impact, deliveries or any reference beyond this card; writing anything but `## Chief`; fixing, verifying or redoing an agent's work; preparing a question; ToolSearch, TodoWrite, resuming an agent.
- Dispatch `prd-flow-<role>` (else `general-purpose` told to follow `.claude/agents/prd-flow-<role>.md`). Prompt: `Slug: <slug>. State: <cwd>/.claude/prd-flow/state/<slug>. Python: <interpreter>. Mode <mode>. <task line or handoff>`. Never paste a briefing. Modes: surveyor `query|light|full|short`; executor `task|fix|close`; reviewer `review`; recheck `recheck`; docs as returned. Task lines: surveyor `case <C1 to C6|unclear> · size <M|L|unclear> · request: <words>`; executor `Plan: <path> · Task: <ID>` or `Card: <state>/card.md`, close `Case <C>`; reviewer `Round N/5. Wave: <n>. Commits: <hashes>`; recheck `Round N/5. Commits: <hashes>. Findings:` <lines>; docs `rules` `Answers:` <the user's words>, then `Confirmed: "<words>"`.
- To the user: context at most 6 lines, a round 25.

## Cases
Every case starts with the surveyor: `query` C1, `light` C2, C3, C4, C6 (or unclear), `full` C5, `short` mid-execution. New behavior in C2, C3 or C6 re-enters as C5.

| Case | When | Route after the surveyor |
|---|---|---|
| C0 no PRD | no PRD | `/prd-create`, `/trd-create`, then the request |
| C1 query | how, why, diagnose | report its return |
| C2 implement | approved rule not met | executor `task`, reviewer, executor `close` |
| C3 bug | code diverges, PRD confirmed | as C2 |
| C4 stale PRD | code right, PRD wrong, confirmed | docs `c4`, executor `close` |
| C5 rule change | new or changed rule, gap, documented defect, new product context | C5 route |
| C6 refactor | structure only | as C2 |

## C5 route
1. Surveyor `full`; it creates the state folder and records the approver.
2. Show the confrontation from `## Survey`; ask: change · keep (C2, C3) · adjust (surveyor `full` again with `Adjust: <the user's words>`).
3. Ask the question rounds of `## Survey`, at most 4 a round; pass the answers verbatim to docs `rules`; show its read-back. Repeat until the user says it is clear and a rule owner agreed.
4. Docs `prd`. Follow its Route (a fan-out returns one `context` route per context). Its return carries the wave table when the gate is green and nothing changed outside the tables; else ask its question first.
5. Ask approval of the wave table (when missing, docs `trd-plan`); an adjustment is docs `trd-plan` with the user's words.
6. Per wave: every executor `task` in one message; then reviewer; recheck after a fix. Then executor `close`; report.

## Returns
Every agent ends with `Status`, `Files:`, `Commit:`, `Route: none|user: <question>|<role> <mode>: <handoff>`, `Next:`. Act on the fields only:
- `done` with `Route: none`: run `Next`.
- `Route: user`: one AskUserQuestion, then `Next` with the answer.
- `Route: <role> <mode>`: dispatch it (one per listed context, in one message), the handoff as the task line.
- `gap` or `blocked` without a Route, or a field missing: the same role once with "return the five fields"; then ask.
- A short C5 (R09) is routes only: follow each `Route` and `Next`, keep the review counter.

| Failure | Dispatch |
|---|---|
| gate red after 2 reruns | the agent's Route |
| promote: missing Source; HTML, archive, final gate; close: a failing step | executor `fix` with the printed lines, then `close`; missing baseline, history-rewrite trailer, drift older than the change: the executor's `Route: user` |
| promote: fold needed | docs `fold`, then executor `close` |
| agent ceiling | same role, new agent, its handoff |
| Critical or High finding | executor `fix`, recheck; Medium, Low pending |
| High that may change a rule | the reviewer's `Route: user`; a change is the short C5 |

Review: at most 5 rounds per delivery; a round is a Critical or High sent to a fix. Say `review: N/5` every round. At round 5 with an open Critical, or a round with more Critical plus High than the previous: stop and ask (extra round, accept with a mitigation, change the rule). Brake: two ceilings, or a wave reported twice as slow: stop, report what is left.

## State
`state/<slug>/state.md`, one writer per section: `## Chief` (you: case, size, phase, decisions one line each, `review: N/5` and last Critical plus High count, wave commits, open finding lines, pending Medium and Low, `Next:`), `## Survey` (surveyor), `## Plan` (docs), `## Close` (executor `close`, before its gate). Update `## Chief` after each return in one Edit (not in C1). Past about 120k tokens or over 2 waves left: save it, offer a fresh session. `/prd-flow resume <slug>`: read only `state.md`, run its `Next:`. Close deletes the folder: report from the `close` return.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests before its time: C5 from step 4, others after confirmation |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only in read-backs |
| R09 | Behavior no approved rule covers: surveyor `short`; more than one rule or a new dimension: full C5 |

Final: case, IDs, commits, plan path, out-of-scope divergences, pending Medium and Low, retro findings.

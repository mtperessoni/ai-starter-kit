---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Loads the PRD rule and TRD map, checks them against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "fix this", "why does it do X", "/prd-flow"). Not for CI, dependency bumps or formatting.
---

# prd-flow

You are the chief: coordinate, never execute a task. Your context is the most expensive of the run and grows with everything you touch, so agents read, write, run and verify. A rule change goes PRD, then TRD, then plan, then code. Prose in the `language` of `repo.md`; IDs in English.

## Chief card
- Do: classify from the surveyor's return, ask the user, dispatch, route by return fields, keep `## Chief` of `state.md`, report.
- Tools, a closed list: Agent dispatch; AskUserQuestion; Read, Write, Edit of `state.md`; Read of `repo.md` once (interpreter, language).
- Forbidden, everything else: Bash (scripts, gates, tests, git); reading PRD, TRD, source, diffs, plan, pack, impact, deliveries or any reference beyond this card; writing anything but `## Chief`; fixing, verifying or redoing an agent's work; reading to prepare a question (the surveyor prepares them); ToolSearch, TodoWrite, resuming an agent.
- Dispatch `subagent_type` `prd-flow-<role>` (without it: `general-purpose` told to follow `.claude/agents/prd-flow-<role>.md`). Prompt: `Slug: <slug>. State: <absolute folder>. Python: <interpreter>. Mode: <mode>. <task line or handoff>`, task line last. Never paste a briefing.
- To the user: context at most 6 lines, a round at most 25.

## Cases
Every case starts with the surveyor: `query` for C1 (its return is the answer), `light` for C2, C3, C4, C6, `full` for C5, `short` mid-execution. Case unclear: `light` with `Case: unclear`; the surveyor decides. New behavior in C2, C3 or C6 re-enters as C5.

| Case | When | Route after the surveyor |
|---|---|---|
| C0 no PRD | surveyor reports no PRD | `/prd-create`, `/trd-create`, then the request |
| C1 query | how, why, diagnose, plan | report its return |
| C2 implement | approved rule not met | executor `task`, reviewer, executor `close` |
| C3 bug | code diverges, PRD confirmed | as C2 |
| C4 stale PRD | code right, PRD wrong, confirmed | docs `c4`, executor `close` |
| C5 rule change | new or changed rule, gap, defect the PRD documents, new product context | C5 route |
| C6 refactor | structure only | as C2 |

## C5 route
1. Surveyor `full` with the request and your case and size (or `unclear`); it creates the state folder and records the approver.
2. Show its confrontation; ask: change · keep (C2, C3) · adjust (surveyor `full` again with `Adjust: <the user's words>`).
3. Ask its prepared questions, at most 4 a round; pass the answers verbatim to docs `rules`; show its read-back. Repeat until the user says it is clear and a named rule owner agreed.
4. Docs `prd`. When its return proves the gate green and no change outside the tables, go on; else ask its question first.
5. Docs `trd-plan`; ask approval of the returned wave table; an adjustment is docs `trd-plan` with the user's words.
6. Per wave of the returned table: every executor `task` in one message; then reviewer with the wave's commit hashes; recheck after a fix.
7. Executor `close`; report.

## Returns
Every agent ends with `Status: done|gap|blocked`, `Files:`, `Commit:`, `Route: none|user: <question>|<role> <mode>: <handoff>`, `Next:`. Act on the fields only:
- `done` with `Route: none`: run `Next`.
- `Route: user`: one AskUserQuestion with that text, then `Next` with the answer.
- `Route: <role> <mode>`: dispatch it, the handoff as the task line.
- `gap` without a Route, or a field missing: the same role once with "return the Route field"; again: ask the user.

| Failure | Dispatch |
|---|---|
| gate red after 2 reruns | the agent's Route: same role fresh with the error lines, or user |
| promote: missing Source | executor `fix`, then executor `close` |
| promote: fold needed | docs `fold`, then executor `close` |
| promote: HTML, archive, final gate | executor `fix` with the printed lines |
| close: any failing step | executor `fix`, then executor `close` |
| agent ceiling | same role, new agent, the return's handoff |
| finding Critical or High | executor `fix`, then recheck; Medium, Low to pending |
| High that may change a rule | the reviewer's `Route: user`; a change is the short C5 |
| invalid return | re-dispatch once, then ask |

Review: at most 5 rounds per delivery; a round counts when Critical or High go to a fix. Say `review: N/5` every round. At round 5 with an open Critical, or a round with more Critical plus High than the previous: stop and ask (an extra round, accept with a mitigation, change the rule). Brake: two ceilings, or a wave twice as slow as the previous: stop and report what is left.

## State
`.claude/prd-flow/state/<slug>/state.md`, one writer per section: `## Chief` (you: case, size, slug, phase, the user's decisions one line each, `review: N/5`, pending Medium and Low, `Next:`), `## Survey` (surveyor), `## Plan` (docs), `## Close` (executor `close`). Update `## Chief` after each return in one Edit. `/prd-flow resume <slug>`: read only `state.md`, then run its `Next:`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests before its time: C5 from step 4, others after confirmation |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only in the read-back |
| R09 | Behavior no approved rule covers: the agent routes it to surveyor `short`; more than one rule or a new dimension: full C5 |

Final: case, IDs, commits, plan path, out-of-scope divergences, pending Medium and Low, the retro findings from the `close` return or "every threshold held".

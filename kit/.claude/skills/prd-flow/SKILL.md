---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Checks the PRD rule and TRD map against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "/prd-flow"). Not for CI or formatting.
---

# prd-flow

You are the chief: coordinate, never execute; agents read, write, run and verify. A rule change goes PRD, TRD, plan, code. Prose in `repo.md` `language`.

## Chief card
- Do: ask, dispatch, route by return fields, keep `## Chief`.
- Tools, closed list: Agent; AskUserQuestion; Read, Write, Edit of `state.md`; Read of `repo.md` once.
- Forbidden, everything else: Bash (no `git log`, no probes); reading PRD, TRD, source, diffs, plan, pack, impact or any reference; writing anything but `## Chief`; fixing, verifying or redoing an agent's work; preparing a question; ToolSearch, TodoWrite.
- Dispatch `prd-flow-<role>` (else `general-purpose` following its `.claude/agents` file). Prompt: `Slug: <slug>. State: <cwd>/.claude/prd-flow/state/<slug>. Python: <`Survey` line; omitted for the first surveyor>. Mode <mode>. <task line or handoff>`. No briefing. Modes: surveyor `query|light|full|short`; executor `task|fix|close`; reviewer `review`; recheck `recheck`; docs as returned. Task lines: surveyor `case <C1 to C6|unclear> · size <M|L|unclear> · request: <words>`; executor `Plan: <path> · Task: <ID>` or `Card: <state>/card.md`, close `Case <C>`; reviewer `Round N/5. Wave: <n|last>. Commits: <hashes>`; recheck `Round N/5. Commits: <hashes>. Findings:` <lines or `findings-r<N>.md` path>; docs `rules` `Answers:` <words>, then `Confirmed: "<words>"`; folded `prd-plan` `Answers:` <words> `Folded: yes`.
- To the user: context 6 lines, round 25.

## Cases
Every case starts with the surveyor: `query` C1, `light` C2, C3, C4, C6 (or unclear), `full` C5, `short` mid-execution. New behavior in C2, C3, C6 is C5.

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
1. Surveyor `full`; it creates the state folder, records the approver.
2. Show the `## Survey` confrontation; ask: change · keep (C2, C3) · adjust (surveyor `full`, `Adjust: <words>`).
3. Ask the question rounds of `## Survey`, at most 4 a round; pass the answers verbatim to docs `rules`; show its read-back. Repeat until the user says it is clear and an owner agreed. Closed = the last round's answers were all prepared options that `## Survey` marks as carrying the full rule text (no Other, no free text), no round left, no `Owner:` question open, no protected question: skip `rules`, step 4 folded.
4. Docs `prd-plan`, once (folded: `Answers:` of every round kept in `## Chief`, `Folded: yes`; it writes rules, PRD, TRD, plan; fan-out: `context` first). It returns the wave table, prose changes and, folded, the rule read-back.
5. One round: approve table, prose and, folded, the read-back. An adjustment is one docs `trd-plan` `adjust: <words>` (folded and a rule changes: it reverts the run's commits and redoes it).
6. From `## Plan` alone: per wave, all executors `task` in one message; reviewer per its `Review:` line; recheck after a fix. Then executor `close`; report.

## Returns
Every agent ends with `Status`, `Files:`, `Commit:`, `Route: none|user: <question>|<role> <mode>: <handoff>`, `Next:`:
- `done` with `Route: none`: run `Next`.
- `Route: user`: one AskUserQuestion, then `Next` with the answer.
- `Route: <role> <mode>`: dispatch it (one per context, one message), the handoff as the task line.
- `gap`/`blocked` without a Route, or a field missing: same role once, "return the five fields"; then ask.
- Short C5 (R09): follow `Route` and `Next`; keep the review counter.

| Failure | Dispatch |
|---|---|
| gate red after 2 reruns | its Route |
| promote: missing Source; HTML, archive, final gate; close: a failing step | executor `fix` with the printed lines, then `close`; missing baseline, history-rewrite trailer, older drift: its `Route: user` |
| promote: fold needed | docs `fold`, then executor `close` |
| agent ceiling | same role, new agent, its handoff |
| Critical or High | executor `fix`, recheck; Medium, Low pending |
| High that may change a rule | its `Route: user`; a change is the short C5 |

Review: at most 5 rounds; a round is a Critical or High sent to a fix. Say `review: N/5`. At round 5 with an open Critical, or a round with more Critical plus High than the previous: stop and ask (extra round, accept with mitigation, change rule). Brake: two ceilings, or `Wave time` twice the last: stop, report.

## State
`state/<slug>/state.md`, one writer per section: `## Chief` (you: case, size, phase, decisions one line each, answers of each round, `review: N/5` and last Critical plus High count, wave commits and `Wave time`, open findings, pending Medium and Low, `Next:`), `## Survey` (surveyor), `## Plan` (docs), `## Close` (executor `close`, before its gate). Update `## Chief` after each return, one Edit (not in C1). Past 120k tokens: offer a fresh session. `/prd-flow resume <slug>`: run its `Next:`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests early: C5 from step 4, others after confirming |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs in read-backs only |
| R09 | Behavior no approved rule covers: surveyor `short`; more than one rule or a new dimension: full C5 |

Final: case, IDs, commits (`Commit:` fields), plan path, out-of-scope divergences, pending Medium/Low, retro findings.

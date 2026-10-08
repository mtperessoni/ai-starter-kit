---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Loads the PRD rule and the TRD map first, checks them against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use whenever someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "fix this", "why does it do X", "/prd-flow"). Not for CI, dependency bumps or formatting.
---

# prd-flow

A rule change goes PRD, then TRD, then plan, then code. When document, code and request disagree, ask citing both sides. Repository values: `repo.md`; prose in its `language`, IDs and code in English.

## Main card
- Read `repo.md` once per session. In a C5, before the surveyor returns, only one Grep of `docs/prd/INDEX.md`.
- Allowed: the confrontation, agent returns, your state files, `git diff --stat`, `git commit` with a file list, one `gate.py --rules`, `promote.py`, one `scripts/gates.sh close`.
- Forbidden: PRD, TRD or source reads before the surveyor; edits under `docs/` or source; diff content; agents' files and references; debugging the gate.
- Inline only what you must hold (answers, returns, short commands); more than about 8k tokens or 3 files you do not need go to an agent.
- Dispatch `subagent_type` `prd-flow-<role>`, prompt `Slug: <slug>. State: <absolute state folder>. Python: <interpreter>. <step or task card>`, task line last. Without them: `general-purpose`, "Read `.claude/agents/prd-flow-<role>.md` and follow it". Never paste a briefing.
- Interview at step 4 right after the confrontation, at most 4 questions a round; formats: `reference/interview.md`.
- At most 2 reruns per step; the third failure is a gap, resolved before the next step.
- In a C5 never call ToolSearch or resume an agent: dispatch a new one.
- Past about 120k tokens or more than 2 waves left: update `state.md`, run `/prd-flow resume <slug>` in a fresh session.
- After plan approval, offer execution in a fresh fast-model session that only dispatches, commits and closes.
- No TodoWrite. To the user: context at most 6 lines, a round at most 25.

## Cases
| Case | When | Agents |
|---|---|---|
| C0 no PRD | No `docs/prd/INDEX.md` | `/prd-create`, `/trd-create`, then the request |
| C1 query | How, why, "diagnose", "plan" | None: IDs, each Source "verified in code" or not; `gate.py --status` |
| C2 implement | Approved rule not met, unwired code included | docs `plan`, executor, reviewer |
| C3 bug | Code diverges, PRD confirmed | executor, reviewer |
| C4 stale PRD | Code right, PRD wrong, confirmed | docs `C4` |
| C5 rule change | New or changed rule, gap, defect the PRD documents, new product context | C5 route |
| C6 refactor | Structure only | executor, reviewer |

State case and size in one line per item. C5 is M, or L with a new data model, contract, integration, technical unknown, area or PRD; other cases are S. Traps: `reference/classification.md`. New behavior in C2, C3 or C6 re-enters as C5.

## Light route
Grep the term in `docs/prd/INDEX.md`, then the rows by ID, the area's map, TRD and cited invariants. C2 to C4: the Source exists, matches the rule and has a caller outside tests; show a divergence side by side and ask. After confirmation (R01), dispatch per Cases, as in step 10.

## C5 route
| Step | Who | Does |
|---|---|---|
| 1 | main | Slug, `scripts/gates.sh context <slug>`, surveyor with case, size, approver (`git config user.name`), request |
| 2 | surveyor | Pack, impact, conflicts, scaffolds of step 4 |
| 3 | main | Show the confrontation; ask: change it (assumed lines confirmed) · do not touch it (C2, C3) · adjust (back to 2) |
| 4 | main | Interview the open dimensions; edit states, answers, rule text, Conflicts resolutions; `gate.py --rules` once, last line into `state.md`; a rule owner other than the approver must agree |
| 5 | docs `C5` | PRD, `docs(prd)`; on to 7 and 8 when green with no non-table changes. Two or more PRDs or TRD areas of over 5 rows each: docs `C5 context` per context, in parallel, then docs `plan` |
| 6 | main | Only if docs stopped: show its gate line and non-table changes; on confirmation, docs `C5 trd+plan` |
| 7, 8 | docs | TRD Planned, plan, wave table |
| 9 | main | Approve from the returned table |
| 10 | executor, reviewer, recheck | Per plan wave: at most 4 executors in one background message, card in the prompt; commit each file list after `git diff --stat`; reviewer per wave, recheck after a Critical or High fix; then `promote.py <slug>`, `scripts/gates.sh close <slug>` |

## State
`.claude/prd-flow/state/<slug>/` (outside git) holds `state.md` (case, size, phase, `review: N/5`) and the agents' files; plan and `decisions.md` live in `changes/NNN-<slug>/`, never truth. Never read `changes/archive/` or legacy `specs/`. Resume reads `state.md` and the current phase file. Scripts run as `<python> .claude/skills/prd-flow/scripts/<name>`.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests before its time: C5 from step 5, other cases after confirmation. A diagnosis is only a diagnosis |
| R02 | Code and PRD answer the facts; the user answers the intent |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R04 | Only the main talks to the user; agents return gaps |
| R05 | At most 5 review rounds per delivery; an open Critical at round 5 goes to the user |
| R06 | Every agent has a ceiling and reports what is left |
| R07 | Questions in product language with a usage example; IDs only in the read-back |
| R08 | Code and TRD follow `docs/code-structure.md`; the ratchet never regresses |
| R09 | Behavior no approved rule covers stops its tasks and enters the short C5 of `reference/execution.md`; more than one rule or a new dimension is a full C5 |

## Files
Main: `repo.md`, `reference/interview.md`, `classification.md`; `execution.md` and `review.md` only for the short C5 and a round-5 stop. Other references: agents only.

Final: case, IDs, commits, plan path, out-of-scope divergences, retro findings of `gates.sh close` or "every threshold held".

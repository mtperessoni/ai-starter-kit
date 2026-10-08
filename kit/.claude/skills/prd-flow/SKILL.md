---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Loads the PRD rule and TRD map, checks them against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "fix this", "why does it do X", "/prd-flow"). Not for CI, dependency bumps or formatting.
---

# prd-flow

A rule change goes PRD, then TRD, then plan, then code. When document, code and request disagree, ask citing both sides: code and PRD answer facts, the user intent. Values: `repo.md`; prose in its `language`, IDs and code in English. `ref/` is `.claude/skills/prd-flow/reference/`.

## Main card
- Read `repo.md` once, `ref/interview.md`, `ref/classification.md`; executing, `ref/execution.md` E01 to E10 and `ref/review.md` V07. Others: agents only.
- Your files: `state.md`, `interview.md`, `approved-rules.md`, `decisions.md` (answers, rule text, resolutions). Allowed: `scripts/gates.sh context|baseline|close <slug>`, `git config user.name`, `git rev-parse HEAD`, `git diff --stat`, `git commit <files>`, `promote.py <slug>`, `gate.py --rules` (one run, at most 2 reruns after fixing your files), `gate.py --step plan` once in a fresh session, `Grep "^### T"` in the plan and each card by range.
- Forbidden: PRD, TRD or source reads before the surveyor (one Grep of `docs/prd/INDEX.md` only); holding over about 8k tokens or 3 files you do not need (dispatch them); edits under `docs/` or source; diff content; agents' files; debugging the gate; `changes/archive/`, legacy `specs/`.
- Dispatch `subagent_type` `prd-flow-<role>`, prompt `Slug: <slug>. State: <absolute state folder>. Python: <interpreter>. <step or task card>`, task line last. Without it: `general-purpose` told to follow `.claude/agents/prd-flow-<role>.md`. Never paste a briefing.
- At most 2 reruns per step; the third failure is a gap, resolved first. No ToolSearch, no agent resume: a new one.
- You update `state.md`: phase, plan path, waves, `review: N/5` for the delivery, pending Medium and Low, one cost line per wave. Checkpoint, fresh session: `ref/execution.md` E01, E02.
- No TodoWrite. To the user: context at most 6 lines, a round at most 25.

## Cases
| Case | When | Agents |
|---|---|---|
| C0 no PRD | No `docs/prd/INDEX.md` | `/prd-create`, `/trd-create`, then the request |
| C1 query | How, why, "diagnose", "plan" | None: IDs and Source |
| C2 implement | Approved rule not met, unwired code included | docs `plan` if over one task, executor, reviewer |
| C3 bug | Code diverges, PRD confirmed | executor, reviewer |
| C4 stale PRD | Code right, PRD wrong, confirmed | docs `C4` |
| C5 rule change | New or changed rule, gap, defect the PRD documents, new product context | C5 route |
| C6 refactor | Structure only | executor, reviewer |

State case and size (`ref/classification.md`) in one line per item; unclear: the surveyor decides. New behavior in C2, C3 or C6 re-enters as C5.

## Light route
Grep the term in `docs/prd/INDEX.md`, then the rows by ID, area map, TRD and invariants. C2 to C4: the Source exists, matches the rule and has a caller outside tests; show a divergence and ask. Confirmed (R01): C2, C3, C6 write a minimal `state.md`, then baseline, executor, reviewer, commit, close without promote.

## C5 route
| Step | Who | Does |
|---|---|---|
| 1 | main | Slug, `gates.sh context`, surveyor with case, size, approver, request; tell the user high effort suits planning |
| 2 | surveyor | Pack, impact, conflicts, contexts, scaffolds of step 4 |
| 3 | main | Show the confrontation; ask: change (assumed lines confirmed) · keep (C2, C3) · adjust (back to 2) |
| 4 | main | Interview the open dimensions, at most 4 questions a round; edit your files; `gate.py --rules`, last line into `state.md`; a distinct owner must agree |
| 5 | docs `C5` | PRD, `docs(prd)`; on to 7 and 8 per the step-6 skip (`ref/prd-writing.md`). Surveyor `fan-out: yes`: docs `C5 context` per context in parallel, then docs `plan` merges |
| 6 | main | Only if docs stopped: show its gate line and non-table changes; on confirmation, docs `C5 trd+plan` |
| 7, 8 | docs | TRD Planned, plan; wave table, plan path to `state.md` |
| 9 | main | Approve from the returned table |
| 10 | executor, reviewer, recheck | Below |

Step 10:
- `scripts/gates.sh baseline <slug>` before wave 1. Per `WAVE` line (`ref/execution.md` E04): `git rev-parse HEAD`, cards in one background message, commit each file list after `git diff --stat`, reviewer on the wave diff.
- Critical is fixed. High is fixed when it fits the approved rules, else asked.
- Medium and Low go to pending; recheck only after a Critical or High fix.
- Close: `promote.py <slug>` (warnings to docs `fold`), commit, `scripts/gates.sh close <slug>`; a passing close deletes the state folder, `deliveries.md` included: promote before close, never after.

## State
`.claude/prd-flow/state/<slug>/` (outside git); plan and `decisions.md` in `changes/NNN-<slug>/`, never truth. Scripts: `<python> .claude/skills/prd-flow/scripts/<name>`.

`/prd-flow resume <slug>` reads `state.md`, then its phase file: confrontation `impact.md`; interview `interview.md`, `approved-rules.md`; docs `writing.md`; execution the wave table, `deliveries.md`. Before step 5, a failing `git diff --quiet <pack Base> -- <pack paths>` means a new surveyor.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests before its time: C5 from step 5, others after confirmation |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only in the read-back |
| R09 | Behavior no approved rule covers stops its tasks and enters the short C5 (`ref/execution.md` E08); more than one rule or a new dimension: full C5 |

Final: case, IDs, commits, plan path, out-of-scope divergences, pending Medium and Low (read from `state.md` before `gates.sh close`), retro findings or "every threshold held".

---
name: prd-flow
description: Mandatory gate for every task that touches product behavior. Loads the PRD rule and TRD map, checks them against the code and, for a rule change, confronts, interviews and confirms before PRD, TRD, plan and code. Use when someone implements, fixes, changes, refactors or asks about a behavior, ticket, bug or feature ("it should", "fix this", "why does it do X", "/prd-flow"). Not for CI, dependency bumps or formatting.
---

# prd-flow

A rule change goes PRD, then TRD, then plan, then code. When document, code and request disagree, ask citing both sides: code and PRD answer facts, the user intent. Values: `repo.md`; prose in its `language`, IDs and code in English. `ref/` is `.claude/skills/prd-flow/reference/`.

## Main card
- Read `repo.md` once, `ref/interview.md`; executing, `ref/execution.md` E01 to E10, E20, `ref/review.md` V07. Others: agents only.
- Your files: `state.md` (phase, `review: N/5`, pending Medium and Low, a cost line per wave), `interview.md`, `approved-rules.md`, `decisions.md`: read them in one message, write them in one message. Allowed: `scripts/gates.sh context|baseline|close <slug>`, `git config user.name`, `git rev-parse HEAD`, per return one Bash `git diff --stat -- <files> && git add <files> && git commit -F -` (due `state.md` lines in it), `promote.py <slug>`, `gate.py --rules`, `gate.py --step plan` once in a fresh session, `Grep "^### T"` in the plan and each card by range.
- Never: PRD, TRD or source before the surveyor (one INDEX Grep only); `impact.md` (the confrontation is in the surveyor's return); over about 8k tokens or 3 files you do not need; edits under `docs/` (ADR included) or source; `git status`, `git log`, diff content (the reviewer reads it); agents' files; compare, lint, ratchet, docs, trailers, retro (inside `gates.sh close`); debugging a gate or script; `changes/archive/`, legacy `specs/`.
- Owners: a failing close, or promote missing a `Source:`, goes to an executor with the error lines; other promote warnings to docs `fold`.
- Dispatch `subagent_type` `prd-flow-<role>`, prompt `Slug: <slug>. State: <absolute state folder>. Python: <interpreter>. <step or task card>`, task line last. Without it: `general-purpose` told to follow `.claude/agents/prd-flow-<role>.md`. Never paste a briefing.
- At most 2 reruns per step; the third failure is a gap, resolved first. No ToolSearch, no TodoWrite, no agent resume: a new one. To the user: context at most 6 lines, a round at most 25.

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

State case and size in one line per item; unclear: the surveyor decides. New behavior in C2, C3 or C6 re-enters as C5.

## Light route
Grep the term in `docs/prd/INDEX.md`, then the rows by ID, area map, TRD and invariants. C2 to C4: the Source exists, matches the rule and has a caller outside tests; show a divergence and ask. Confirmed (R01): C2, C3, C6 write a minimal `state.md`, then baseline, executor, reviewer, commit, close without promote.

## C5 route
| Step | Who | Does |
|---|---|---|
| 1 | main | Slug, `gates.sh context`, surveyor with case, size (or `unclear`), approver, request; it creates the state folder |
| 2 | surveyor | Pack, impact, conflicts, protected rules, contexts, scaffolds of step 4 |
| 3 | main | Show the confrontation; ask: change (assumed lines confirmed) · keep (C2, C3) · adjust (back to 2) |
| 4 | main | Interview the open dimensions, at most 4 questions a round; edit your files; `gate.py --rules`, last line into `state.md`; a distinct owner must agree |
| 5 | docs `C5` | PRD (and the ADR `state.md` names), `docs(prd)`; on to 7 and 8 per the step-6 skip. `fan-out: yes`: docs `C5 context` per context in parallel, then docs `plan` |
| 6 | main | Only if docs stopped: show its gate line and non-table changes; on confirmation, docs `C5 trd+plan` |
| 7, 8 | docs | TRD Planned, plan; wave table, steps, plan path to `state.md` |
| 9 | main | Approve from the returned table |
| 10 | executor, reviewer, recheck | Below |

Step 10 is the execution line of "State". Per `WAVE` line (E04): `git rev-parse HEAD`, cards in one background message; a card's `Lens:` only adds a reviewer. Critical is fixed; High too when it fits the approved rules, else asked; Medium and Low to pending. Close deletes the state folder: promote first.

## State
`.claude/prd-flow/state/<slug>/` (outside git); plan and `decisions.md` in `changes/NNN-<slug>/`, never truth. Scripts: `<python> .claude/skills/prd-flow/scripts/<name>`.

`/prd-flow resume <slug>` reads `state.md`, then its phase file: confrontation `impact.md`; interview `interview.md`, `approved-rules.md`; docs `writing.md`; execution the wave table and `deliveries.md`, then: `gates.sh baseline`; per wave: dispatch executors, commit, `prd-flow-reviewer` always, recheck after a Critical or High fix; `promote.py`; commit; `gates.sh close`. Before step 5, a failing `git diff --quiet <pack Base> -- <pack paths>` means a new surveyor.

## Rules
| ID | Rule |
|---|---|
| R01 | Nothing in `docs/`, source or tests before its time: C5 from step 5, others after confirmation |
| R03 | No em dash (U+2014). Push and PR only on explicit request |
| R07 | Questions in product language with an example; IDs only in the read-back |
| R09 | Behavior no approved rule covers stops its tasks and enters the short C5 (E08); more than one rule or a new dimension: full C5 |

Final: case, IDs, commits, plan path, out-of-scope divergences, pending Medium and Low (from `state.md` before close), the retro findings close printed or "every threshold held".

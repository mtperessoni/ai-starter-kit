# Code review (execution of C2, C3, C5 and C6)

Review is what catches the serious defect before the user does, and it must run. What this page prevents is the cycle review, fix and review again becoming a loop: each open round finds a new edge case, and fixing one finding opens the surface for the next. Read by the reviewer, the recheck, the executor in `fix` mode and the maintainer; the chief acts on their return fields through its card in `SKILL.md` and never reads this page, a diff or a finding's code.

## Review table
| Moment | Who | Over what |
|---|---|---|
| Every wave of a C5 plan with a parallel wave, and the standalone task of C2, C3, C6; a serial C5 plan (every wave one task) is reviewed once after the last wave (`Wave: last`); whatever the cards' `Lens:` says (a lens only adds a rubric) | `prd-flow-reviewer`, one round | the combined diff from the commit hashes the chief passes (one wave, or all the waves for `Wave: last`), the rule IDs, the `Decisions:` rows and the `Leave:` items of those cards |
| After a fix of a Critical or High | `prd-flow-recheck`, a second round | only the fix diff and the previous finding IDs |
| Medium and Low of a round | one batched `executor fix` dispatch (RV18) | the finding lines together, with the Critical and High fixes when there are any; no re-review of the Medium and Low |
| The fix of round 5 | `prd-flow-recheck` | a scoped check of that fix; it is not a round 6 |

## Routing by return
The reviewer and the recheck decide, the chief only follows the fields:

| Return | Chief dispatches |
|---|---|
| reviewer, no Critical, High or Medium | `Route: none`; Low listed in the return goes to the pending list of `## Chief`; `Next` is the next wave or executor `close` |
| reviewer, Critical, High or Medium within the approved rules | one `Route: executor fix: <finding lines of every severity of the round, Owns, Read, rule IDs>`; then, when it fixed a Critical or High, the recheck with the finding IDs and the fix commit |
| reviewer, a High that may change a rule | `Route: user: <the question in product language, options>`; a change is the short C5 (V06) |
| recheck, all resolved | `Route: none`; the wave is closed |
| recheck, a finding still open | `Route: executor fix` again, counted as a new round (V01) |

## Rules
| ID | Rule |
|---|---|
| V01 | A **round** is counted when Critical, High or Medium findings are sent back for a fix (RV18). Every wave of a plan with a parallel wave (one review after the last wave for a serial plan), and the standalone task of C2, C3, C6, gets a review, but a wave review with only Low findings, or none, costs no round. The stop of V07 applies to the delivery |
| V02 | **At most 5 rounds per delivery.** The chief keeps one `review: N/5` in `## Chief` (each round's wave and findings by severity, one line; a Medium round counts) and tells the user every round |
| V03 | The first review of a wave covers the combined wave diff. A second round happens only after a Critical or High fix, and it is **scoped**: it only checks the previous findings against the fix diff, and only points out new problems that diff created. Never "list any new problem" outside it |
| V04 | Severity policy, decided by the reviewer in its Route: Critical is fixed; High is fixed when it fits the approved rules, else it goes to the user; Medium and Low of the round go to one batched fix dispatch (a Medium alone sends the round to a fix and counts toward the cap; Low alone stays pending), never re-reviewed; recheck only after a Critical or High fix |
| V05 | **Cascade:** if a round finds more Critical plus High than the previous one, the chief stops before the next round and talks to the user (V07). A fix that raises the risk is a sign of a design cause, not of one more patch |
| V06 | **Any behavior change during execution** (a case no rule covers, a new rule, and always the safety posture: removing a guard, a net, a list, a switch) is not one more task: the agent returns `Route: surveyor short` and the short C5 of `execution.md` (E08 to E10) follows, with what the net covered on the table before code. The counter does not reset by itself; only with explicit approval |
| V07 | **At round 5 (of the delivery) with an open Critical, or in a cascade (V05): the chief stops and asks.** Each Critical in plain language (what happens to the user), from the reviewer's return, with the options: an authorized extra round for that finding; accept the risk with a recorded mitigation; change the rule (back to C5). Never fire round 6 without an explicit yes |
| V08 | **Ceiling per agent (the single home of these numbers; every other file cites V08):** executor, fixer, surveyor and docs agent stop at about 50 tool calls or 30 minutes, reviewer at 40 calls, the scoped re-check (`prd-flow-recheck`) at about 15, and return what they did and what is left as a handoff. The chief replaces it with a new agent of the same role (execution.md E14). A scoped re-check goes with the closed list of files and the fix commit |
| V09 | The full suite runs once, as `compare` during the last review (execution.md E18); the reviewer reads the executors' Self-check first, then the diff, and runs nothing; the wave verification (`gates.sh verify`) runs beside it, started by the chief; an executor runs only its own new test |
| V10 | Fixing runs through executor `fix`: the finding lines are its card, with the files it may change (Owns), what to read and the rule IDs. The reviewer returns one line per finding, at most 8 |

## Record in `## Chief`
```markdown
review: 2/5
- wave 1 · round 1 · 0 Critical, 3 High · fix
- wave 1 · round 2 · 0 Critical, 0 High, 1 Medium · closed
- wave 2 · no round · 0 blocking · closed
Pending: CS-004 Medium (wave 1)
```

# Code review (execution of C2, C3, C5 and C6)

Review is what catches the serious defect before the user does, and it must run. What this page prevents is the cycle review, fix and review again becoming a loop: each open round finds a new edge case, and fixing one finding opens the surface for the next.

## Rules
| ID | Rule |
|---|---|
| V01 | A **round** is: the delivery's reviewers run over a diff and the blocking findings are fixed. It counts per delivery (the whole plan, or the standalone task of C2, C3, C6), not per task |
| V02 | **At most 5 rounds per delivery.** The counter lives in `state.md` (`review: N/5`, with each round's findings by severity) and is told to the user every round |
| V03 | Round 1 reviews the delivery diff. From round 2 the re-review is **scoped**: it only checks the previous round's findings against the fix diff, and only points out new problems that diff created. Never "list any new problem" outside it |
| V04 | **Critical** blocks and is fixed. **High** is fixed when the fix fits the approved rules; otherwise it becomes a question to the user. **Medium and Low** become pending items in `state.md` and the user decides if and when to fix them |
| V05 | **Cascade:** if a round finds more Critical plus High than the previous one, stop before the next round and talk to the user (V07). A fix that raises the risk is a sign of a design cause, not of one more patch |
| V06 | **A decision during execution that changes the safety posture** (removing a guard, a net, a list, a switch) is not one more task: it follows the short C5 of `reference/execution.md` (E08 to E10), with what the net covered on the table before code. The counter does not reset by itself; only with explicit approval |
| V07 | **At round 5 with an open Critical, or in a cascade (V05): stop and talk.** Show each Critical in plain language (what happens to the user) with the options: an authorized extra round for that finding; accept the risk with a recorded mitigation; change the rule (back to C5). Never fire round 6 without an explicit yes |
| V08 | **Ceiling per agent:** executor and fixer stop at about 50 tool calls or 30 minutes, reviewer at 40 calls, and report what they did and what is left (`reference/workers.md`, sections `executor` and `reviewer`). An agent that stopped at the ceiling reports; it is not resumed in a loop: work continues in a new agent with a short handoff (execution.md E14). A scoped re-review goes with the closed list of files and the fix diff |
| V09 | The full suite runs a single time, at the end of all tasks (execution.md E18); a wave review reads the diff, it does not run the suite; inside a task, only the tests related to the module written (the mirror and those that import or use it) |
| V10 | Fixing the findings runs through the `executor` worker, with the finding IDs in place of the task ID; the request to the reviewer follows the `reviewer` section (one line per finding, at most 8) |

## Record format in `state.md`
```markdown
## Review (V02)
| Round | Diff | Critical | High | Medium | Low | Decision |
|---|---|---|---|---|---|---|
| 1/5 | abc123..def456 | 0 | 3 | 0 | 0 | fix the 3 High |
| 2/5 | def456..0a1b2c | 0 | 0 | 1 | 0 | Medium goes to pending; delivery closed |
```

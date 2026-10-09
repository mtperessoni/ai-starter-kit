# Code review with a ceiling (RV)

Review must run: it is what catches the serious defect before users do. What these rules prevent is the cycle review, fix, review again turning into a loop where each open round finds a new edge case and each fix opens the surface for the next one.

The V-labels below live in prd-flow `reference/run.md` "Review" (decision L18).

| ID | Rule | Why | Lands in |
|---|---|---|---|
| RV01 | A **round** is counted when Critical or High findings of a review over one diff are sent back for a fix (RV18). Rounds count per delivery (the whole plan, or a standalone task), not per task; a wave review with only Medium and Low findings, or none, costs no round | Counting per task hides the total; Medium alone counted as a round spent the cap of 5 on polish (one-pass interview branch, 2026-10-09) | run.md V01 |
| RV02 | **At most 5 rounds per delivery.** The counter lives in `state.md` as `review: N/5`, with each round's findings by severity, and is told to the user every round | The user chose 5; an unbounded loop once consumed 3.6 of 8.8 agent hours | run.md V02; SKILL.md "Review" |
| RV03 | Round 1 reviews the delivery diff. From round 2 the re-review is **scoped**: it checks the previous round's findings against the fix diff and reports only new problems that diff created. It is done by the warm reviewer of the round, resumed with the fix commit (L7); `prd-flow-recheck` stays as the cold fallback when that reviewer is gone or past its ceiling. Never "list any new problem" outside the scope | Open-ended re-review always finds something; a cold recheck per round was one more cold start (L7) | run.md V03; `prd-flow-reviewer.md` `recheck` |
| RV04 | **Critical** blocks and is fixed. **High** is fixed when the fix fits the approved rules; otherwise it becomes a question to the user. **Medium** goes to the round's one batched fix (RV18); **Low** becomes a pending item in `state.md` and the user decides if and when | Severity decides the path; not everything is blocking | run.md V04 |
| RV05 | **Cascade:** if a round finds more Critical plus High than the previous one, stop before the next round and talk to the user | A fix that raises risk signals a design cause, not one more patch | run.md V05; SKILL.md "Review" |
| RV06 | A decision during execution that changes the safety posture (removing a guard, a net, a list, a switch) is never an extra task: it follows the short rule-change route, with what the net covered on the table before code. The counter resets only with explicit approval | Safety changes disguised as fixes are how protections disappear | run.md V06; WF12 |
| RV07 | At round 5 with an open Critical, or in a cascade: stop and talk. Show each Critical in plain language (what happens to the user) with options: an authorized extra round for that finding; accept the risk with a recorded mitigation; change the rule (back to rule change). Never fire round 6 without an explicit yes | The user owns risk acceptance | run.md V07; SKILL.md "Review" |
| RV08 | Ceilings per agent: executor and fixer about 50 calls or 30 minutes, reviewer about 40 calls; the surveyor `full` and docs `apply` about 80 calls (L10). An agent that stopped at its ceiling reports and is not resumed in a loop; work continues in a new agent with a short handoff. `run.md` V08 is the single home of the numbers | Same as SA15, SA16; the full survey and the one-pass apply are bigger jobs than the rest (L10) | run.md V08 |
| RV09 | The full suite runs once, at the end of all tasks. A wave review reads the diff, it does not run the suite; inside a task, only its own new test; related tests per wave via `gates.sh verify` | Reviews running the suite cost minutes per round | run.md V09; TS03 |
| RV10 | Fixes go to the warm executor of the task (SendMessage with the finding lines); a new executor `fix` only when that agent is past its ceiling or about 150k tokens (L7). The reviewer request follows the `reviewer` section: one line per finding, at most 8 | Same worker, same discipline, same return format; a cold executor per fix reread the files it had just written (L7) | run.md "Fix", V10; dispatch.md DP03 |
| RV11 | Finding format: `[Critical\|High\|Medium\|Low] CS-NNN · file:line · rule · concrete scenario in one sentence · fix in one sentence`. Severity by consequence to the user or the delivery, not elegance. "Possible in theory" without a concrete scenario is Low | Uniform, rankable, cheap findings | `prd-flow-reviewer.md`; run.md "Review" |
| RV12 | Reviewers are findings-only agents: they never edit code or write files; their Bash is read-only git (`diff`, `log`, `show`, `status`, `merge-base`, `rev-parse`), no test runs, no installs | Separation of judging and fixing keeps rounds countable | `.claude/agents/*-reviewer.md` |
| RV13 | One reviewer per risk class of the domain (for example safety, contract compatibility), each guarding one principle of the constitution, with a fixed list of checks it must run and report as passed, violated or not applicable | A focused reviewer finds the class of bug that costs the most; a generic one skims | `docs/templates/reviewer-agent.md` (copied to `.claude/agents/<risk>-reviewer.md`) |
| RV14 | Prove it or drop it: every finding cites a real file and line from the diff or the code it reaches, with a failure scenario told with real values; no "could potentially lead to issues" | Unprovable findings train the team to ignore the reviewer | reviewer template |
| RV15 | Say so when it is clean: a clean review states what was checked and that it passed; never pad with speculative findings | The reviewer's credibility is the control | reviewer template |
| RV16 | The agent description carries 3 or 4 examples of when to invoke it, each with a short commentary of why | Routing precision: the right reviewer is picked for the diff | reviewer template |
| RV17 | CI runs an automated Claude review on every pull request, over the changed files only, after reading the constitution, `CLAUDE.md` and `AGENTS.md`, with severity labels and "only real issues" | A second net on every PR at no human cost | `.github/workflows/claude-review.yml` |
| RV18 | **One batched fix per round, review per wave stays:** the Medium and Low findings of a round go to one fix dispatch together with the Critical and High ones; Medium and Low alone stay pending; they are never re-reviewed, only a Critical or High fix gets a recheck and counts toward the cap of 5. Amends RV01 | Medium findings went to pending and came back as a second fix dispatch, and fixes were scattered one finding at a time (metrics `review_rounds`, `rework_actions`; G5 targets fix dispatches down 40%) | run.md V01, V02, V04; SKILL.md "Review" |

Record in `state.md`:

```markdown
## Review (V02)
| Round | Diff | Critical | High | Medium | Low | Decision |
|---|---|---|---|---|---|---|
| 1/5 | abc123..def456 | 0 | 3 | 0 | 0 | fix the 3 High |
| 2/5 | def456..0a1b2c | 0 | 0 | 1 | 0 | Medium goes to pending; delivery closed |
```

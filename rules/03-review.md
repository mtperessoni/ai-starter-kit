# Code review with a ceiling (RV)

Review must run: it is what catches the serious defect before users do. What these rules prevent is the cycle review, fix, review again turning into a loop where each open round finds a new edge case and each fix opens the surface for the next one.

| ID | Rule | Why | Lands in |
|---|---|---|---|
| RV01 | A **round** is: the delivery's reviewers run over one diff, and the blocking findings are fixed. Rounds count per delivery (the whole plan, or a standalone task), not per task | Counting per task hides the total | review.md V01 |
| RV02 | **At most 5 rounds per delivery.** The counter lives in `state.md` as `review: N/5`, with each round's findings by severity, and is told to the user every round | The user chose 5; an unbounded loop once consumed 3.6 of 8.8 agent hours | review.md V02 |
| RV03 | Round 1 reviews the delivery diff. From round 2 the re-review is **scoped**: it checks the previous round's findings against the fix diff and reports only new problems that diff created. Never "list any new problem" outside it | Open-ended re-review always finds something | review.md V03 |
| RV04 | **Critical** blocks and is fixed. **High** is fixed when the fix fits the approved rules; otherwise it becomes a question to the user. **Medium** and **Low** become pending items in `state.md` and the user decides if and when | Severity decides the path; not everything is blocking | review.md V04 |
| RV05 | **Cascade:** if a round finds more Critical plus High than the previous one, stop before the next round and talk to the user | A fix that raises risk signals a design cause, not one more patch | review.md V05 |
| RV06 | A decision during execution that changes the safety posture (removing a guard, a net, a list, a switch) is never an extra task: it follows the short rule-change route, with what the net covered on the table before code. The counter resets only with explicit approval | Safety changes disguised as fixes are how protections disappear | review.md V06; WF12 |
| RV07 | At round 5 with an open Critical, or in a cascade: stop and talk. Show each Critical in plain language (what happens to the user) with options: an authorized extra round for that finding; accept the risk with a recorded mitigation; change the rule (back to rule change). Never fire round 6 without an explicit yes | The user owns risk acceptance | review.md V07 |
| RV08 | Ceilings per agent: executor and fixer about 50 calls or 30 minutes, reviewer about 40 calls. An agent that stopped at its ceiling reports and is not resumed in a loop; work continues in a new agent with a short handoff | Same as SA15, SA16 | review.md V08 |
| RV09 | The full suite runs once, at the end of all tasks. A wave review reads the diff, it does not run the suite; inside a task, only related tests | Reviews running the suite cost minutes per round | review.md V09; TS03 |
| RV10 | Fixes run through the `executor` worker with the finding IDs in place of a task ID. The reviewer request follows the `reviewer` section: one line per finding, at most 8 | Same worker, same discipline, same return format | review.md V10 |
| RV11 | Finding format: `[Critical\|High\|Medium\|Low] CS-NNN · file:line · rule · concrete scenario in one sentence · fix in one sentence`. Severity by consequence to the user or the delivery, not elegance. "Possible in theory" without a concrete scenario is Low | Uniform, rankable, cheap findings | `prd-flow-reviewer.md` |
| RV12 | Reviewers are findings-only agents: they never edit code or write files; their Bash is read-only git (`diff`, `log`, `show`, `status`, `merge-base`, `rev-parse`), no test runs, no installs | Separation of judging and fixing keeps rounds countable | `.claude/agents/*-reviewer.md` |
| RV13 | One reviewer per risk class of the domain (for example safety, contract compatibility), each guarding one principle of the constitution, with a fixed list of checks it must run and report as passed, violated or not applicable | A focused reviewer finds the class of bug that costs the most; a generic one skims | `docs/templates/reviewer-agent.md` (copied to `.claude/agents/<risk>-reviewer.md`) |
| RV14 | Prove it or drop it: every finding cites a real file and line from the diff or the code it reaches, with a failure scenario told with real values; no "could potentially lead to issues" | Unprovable findings train the team to ignore the reviewer | reviewer template |
| RV15 | Say so when it is clean: a clean review states what was checked and that it passed; never pad with speculative findings | The reviewer's credibility is the control | reviewer template |
| RV16 | The agent description carries 3 or 4 examples of when to invoke it, each with a short commentary of why | Routing precision: the right reviewer is picked for the diff | reviewer template |
| RV17 | CI runs an automated Claude review on every pull request, over the changed files only, after reading the constitution, `CLAUDE.md` and `AGENTS.md`, with severity labels and "only real issues" | A second net on every PR at no human cost | `.github/workflows/claude-review.yml` |

Record in `state.md`:

```markdown
## Review (V02)
| Round | Diff | Critical | High | Medium | Low | Decision |
|---|---|---|---|---|---|---|
| 1/5 | abc123..def456 | 0 | 3 | 0 | 0 | fix the 3 High |
| 2/5 | def456..0a1b2c | 0 | 0 | 1 | 0 | Medium goes to pending; delivery closed |
```

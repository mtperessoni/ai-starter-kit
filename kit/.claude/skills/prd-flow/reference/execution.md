# Execution (C5 step 10, and C2, C3, C6 with code)

Read only by whoever executes. The main thread dispatches, commits and decides; the work goes to the `executor` and `reviewer` workers (`reference/workers.md`). Commands come from `repo.md`.

## Where to execute
| ID | Rule |
|---|---|
| E01 | A plan with more than 6 tasks, or touching a big file from `repo.md`: execute in a new session, with `/prd-flow resume <slug>`, starting from `state.md` and the plan. The C5 session already carries the confrontation, the interview and the writing, and every agent report adds to that |
| E02 | A smaller plan may continue in the same session |

## Order
| ID | Step |
|---|---|
| E03 | Baseline: the failures of the last recorded full run go to `state/<slug>/baseline-failures.txt` (with none recorded, the full suite runs once before code). At the end (E18), only new failures count |
| E04 | Per wave: tasks with disjoint Owns run in parallel; a big file has a serial chain. Each task goes to the `executor` with a one-line prompt (*"task T07 of plan `<path>`"*), on the model the plan marks |
| E05 | Each return: check the diff of the listed files and commit only those, with the message the executor proposed. A gap that is a rule or contract divergence goes to the short C5 (R09, E08 to E10); only a missing technical detail becomes a question to the user or a new task, resolved before the task that depends on it. The proposed message carries the `Rules:` or `Case: none (...)` trailer |
| E06 | End of the wave: review by the `reviewer` with the ceiling of `reference/review.md` (at most 5 rounds; fixes by the `executor` with the finding IDs) |
| E07 | To continue an agent's work, resume it (SendMessage); do not open another one, which would reread everything. An agent the user interrupted is not resumed: first save what it left with `git --no-pager diff` into a patch in `state/<slug>/` |

## Rule change in the middle of execution (short C5, R09)
The trigger and the stop are R09 (SKILL.md).

| ID | Step |
|---|---|
| E08 | Stop the tasks that touch the behavior (review.md V06) and dispatch the `surveyor` in short mode: K01, K02, K11, K12 on the touched rules only, confrontation of at most 15 lines in product language (R07). Show the current rule and the proposal and ask. Outside a C5 (during C2, C3 or C6) first create what step 4 creates: `interview.md` (first line `Scope: short C5 outside a C5`, then a dated Dimensions table of only the reopened dimensions; without that line the gate requires D01 to D15), `approved-rules.md`, and the change folder `changes/NNN-<slug>/` with `decisions.md` and `plan.md`. More than one rule, or a dimension the original change never covered: re-enter as a full C5 |
| E09 | Interview of the reopened dimensions only: a dated `## Dimensions (YYYY-MM-DD)` table in `interview.md` with its own `Confirmed:` line (at least one dimension), and new `DEC-` rows in `decisions.md` |
| E10 | Approved: append a dated section to `approved-rules.md` (`## YYYY-MM-DD`, then `### <prd file>.md` and its rows; a re-approved ID replaces its earlier row, the gate takes the latest; old text literal for the CHANGELOG) and dispatch `writer-prd` with *"apply the YYYY-MM-DD section of approved-rules.md"* (`--applied` green), then `writer-trd`, then the `planner` only appends the new tasks to the plan (outside a C5, to the `plan.md` E08 created); execution resumes. No hand edits of PRD, HTML or CHANGELOG. The review counter does not reset without explicit approval |

## Cost per agent
The weight of an agent is the context it resends on every call, times the number of calls. An executor with 300k tokens and 150 calls costs more than the rest of the route.

| ID | Rule |
|---|---|
| E12 | No worker opens a subagent. Parallelism belongs only to the main thread, by wave |
| E13 | Executor and fixer run on `sonnet`. `opus` only when the plan marks the task as a new safety decision (or another reason written on the task line) |
| E14 | An agent that hit its ceiling, or passed about 150k tokens, is not resumed: the main thread opens a new agent with a handoff of at most 10 lines (files touched, red tests, next step). This prevails over E07 |
| E15 | The worker prompt names the task's files, entry symbols and tests; it does not reread the whole plan, only its section |
| E16 | Tests run with output redirected to a file, and only the `FAILED` and `ERROR` lines and the summary come back into context |
| E17 | Brake: an agent that hits its ceiling twice, or a wave that takes more than twice the time of the previous one, stops the execution and goes to the user with what is left and the cost so far. Never run for hours without reporting |
| E18 | **Tests only at the end.** During execution no agent runs the full suite: the executor runs only the tests related to what it touched, the mirror file and those that import or use the touched module (`Grep` of the module path in the test folders), with the single-file command of `repo.md` (no coverage). A failure in a test unrelated to what it touched is not investigated midway: it waits for the end. The full suite runs a single time, after all tasks are applied; then a closing task fixes the tests and the code that are wrong according to the PRD |
| E19 | **Moving code is done by script.** In a refactor the agent decides the map (which symbol goes to which module) and a script cuts and pastes the blocks by line range or AST; the model only fixes imports and calls. Never retype a function body: it is slow and creates transcription errors. With huge test files, split code and tests first and prove statically (import check, type check, lint); run tests in parts afterwards |
| E20 | **Retro at the end.** After the full suite (E18), run `scripts/gates.sh retro`. The final report lists each finding (severity, value, threshold, evidence) or says the run stayed within every threshold. The retro is read-only evidence: findings become tasks only when the user asks. The recording is silent and no agent turns it on or off |

## Cost record
| ID | Rule |
|---|---|
| E11 | At the end of each wave, append one line to `state.md`: wave, agents dispatched, review rounds, the most expensive agent (tokens and minutes). It is the baseline to compare one execution with the next and to know whether the process got cheaper |

```markdown
## Cost (E11)
| Wave | Agents | Reviews | Most expensive |
|---|---|---|---|
| 1-A | 6 | 1/5 | T04 · 120k tokens · 9 min |
```

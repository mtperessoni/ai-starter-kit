# Execution (C5 step 10, and C2, C3, C6 with code)

Read only by whoever executes. The main thread dispatches, commits and decides; the work goes to the `prd-flow-executor` and `prd-flow-reviewer` agents. Commands come from `repo.md`.

## Where to execute
| ID | Rule |
|---|---|
| E01 | Checkpoint: past about 120k tokens in the main, or with more than 2 waves left, write `state.md` and continue in a fresh session with `/prd-flow resume <slug>` (it starts from `state.md` and the plan) |
| E02 | After the plan is approved and committed, execution may continue in a fresh session on the fast model: the main only dispatches, commits and closes there |

## Order
| ID | Step |
|---|---|
| E03 | Baseline: the failures of the last recorded full run go to `state/<slug>/baseline-failures.txt` (with none recorded, the full suite runs once before code). At the end (E18), only new failures count |
| E04 | Waves come from `gate.py --step plan` (the `WAVE n:` lines). At most 4 executors per wave, dispatched in one message in the background; no polling, the returns arrive by themselves. Dispatch by agent type `prd-flow-executor`, the prompt carrying the slug, the state folder, the interpreter and the task card (at most 25 lines); the model is the one the card marks. A failed task reruns alone. On rate limits the wave shrinks to 2. A big file has a serial chain |
| E05 | Each return: check only `git diff --stat` against the file list the executor returned (the reviewer reads content), and commit those files with the message the executor proposed. A gap that is a rule or contract divergence goes to the short C5 (R09, E08 to E10); only a missing technical detail becomes a question to the user or a new task, resolved before the task that depends on it. The message carries the `Rules:` or `Case: none (...)` trailer |
| E06 | Every wave gets one review by the `prd-flow-reviewer` on the combined wave diff, with the ceiling of `reference/review.md` (a one-task wave included). Fixes go to a `prd-flow-executor` with the finding IDs |
| E07 | An agent is never resumed: continuing its work is a new agent with the pack, the state files and a handoff when needed. An agent the user interrupted: first save what it left with `git --no-pager diff` into a patch in `state/<slug>/` |

## Rule change in the middle of execution (short C5, R09)
The trigger and the stop are R09 (SKILL.md).

| ID | Step |
|---|---|
| E08 | Stop the tasks that touch the behavior (review.md V06) and dispatch the `prd-flow-surveyor` in short mode: K01, K02, K11, K12 on the touched rules only, confrontation of at most 15 lines in product language (R07). Show the current rule and the proposal and ask. Outside a C5 (during C2, C3 or C6) first create what step 4 creates: `interview.md` (first line `Scope: short C5 outside a C5`, then a dated Dimensions table of only the reopened dimensions; without that line the gate requires D01 to D15), `approved-rules.md`, and the change folder `changes/NNN-<slug>/` with `decisions.md` and `plan.md`. More than one rule, or a dimension the original change never covered: re-enter as a full C5 |
| E09 | Interview of the reopened dimensions only: a dated `## Dimensions (YYYY-MM-DD)` table in `interview.md` with its own `Confirmed:` line (at least one dimension), and new `DEC-` rows in `decisions.md` |
| E10 | Approved: append a dated section to `approved-rules.md` (`## YYYY-MM-DD`, then `### <prd file>.md` and its rows; a re-approved ID replaces its earlier row, the gate takes the latest; old text literal for the CHANGELOG) and dispatch the `prd-flow-docs` agent with *"apply the YYYY-MM-DD section of approved-rules.md"* (`--applied` green), then TRD, and the plan only gets the new tasks appended (outside a C5, to the `plan.md` E08 created); execution resumes. No hand edits of PRD, HTML or CHANGELOG. The review counter does not reset without explicit approval |

## Cost per agent
The weight of an agent is the context it resends on every call, times the number of calls. An executor with 300k tokens and 150 calls costs more than the rest of the route.

| ID | Rule |
|---|---|
| E12 | No agent opens a subagent. Parallelism belongs only to the main thread, by wave |
| E13 | Executor and fixer run on `sonnet`. `opus` only when the plan marks the task as a new safety decision (or another reason written on the task line) |
| E14 | An agent that hit its ceiling, or passed about 150k tokens, is replaced by a new agent with a handoff of at most 10 lines (files touched, red tests, next step). At most 2 reruns per step; the third failure becomes a gap that returns the ERROR lines |
| E15 | The agent prompt names the task's files, entry symbols and tests (its card); it does not reread the whole plan, only its section |
| E16 | Tests run with output redirected to a file, and only the `FAILED` and `ERROR` lines and the summary come back into context |
| E17 | Brake: an agent that hits its ceiling twice, or a wave that takes more than twice the time of the previous one, stops the execution and goes to the user with what is left and the cost so far. Never run for hours without reporting |
| E18 | **Tests only at the end.** During execution no agent runs the full suite: the executor runs only the tests related to what it touched, the mirror file and those that import or use the touched module (`Grep` of the module path in the test folders), with the single-file command of `repo.md` (no coverage). A failure in a test unrelated to what it touched is not investigated midway: it waits for the end. The full suite runs a single time, after all tasks are applied; then a closing task fixes the tests and the code that are wrong according to the PRD |
| E19 | **Moving code is done by script.** In a refactor the agent decides the map (which symbol goes to which module) and a script cuts and pastes the blocks by line range or AST; the model only fixes imports and calls. Never retype a function body: it is slow and creates transcription errors. With huge test files, split code and tests first and prove statically (import check, type check, lint); run tests in parts afterwards |
| E20 | **Closing.** After the last wave and its review: run `promote.py <slug>` (drops markers, fills Source, writes the CHANGELOG, rebuilds the HTML, archives the change folder), commit its result, then `scripts/gates.sh close <slug>` (full suite against the baseline, lint, trailers, `gate.py --final`, retro). The final report lists each retro finding (severity, value, threshold, evidence) or says the run stayed within every threshold; findings become tasks only when the user asks. The recording is silent and no agent turns it on or off |

## Deliveries and cost record
| ID | Rule |
|---|---|
| E21 | `deliveries.md` is always at `.claude/prd-flow/state/<slug>/deliveries.md`: one block per finished task (at most 8 lines: what was created, the symbols later tasks consume, the `Source:` files). A consumer reads the producer's block, never its code |
| E11 | At the end of each wave, append one line to `state.md`: wave, agents dispatched, review rounds, the most expensive agent (tokens and minutes). It is the baseline to compare one execution with the next |

```markdown
## Cost (E11)
| Wave | Agents | Reviews | Most expensive |
|---|---|---|---|
| 1-A | 6 | 1/5 | T04 · 120k tokens · 9 min |
```

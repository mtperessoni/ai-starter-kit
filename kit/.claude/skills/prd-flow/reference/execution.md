# Execution (C5 step 10, and C2, C3, C6 with code)

Read only by whoever executes. The main thread dispatches, commits and decides; the work goes to the `prd-flow-executor` and `prd-flow-reviewer` agents. Commands come from `repo.md`.

## Where to execute
| ID | Rule |
|---|---|
| E01 | Checkpoint (the single home of these numbers): past about 120k tokens in the main, or with more than 2 waves left, update `state.md` and continue in a fresh session with `/prd-flow resume <slug>`. The fresh session starts from `state.md` only: phase, plan path, wave table, `review: N/5` per wave, pending items, cost lines |
| E02 | After the plan is approved and committed, offer execution in a fresh session on the fast model: the main only dispatches, commits and closes there. To build a prompt it Greps `^### T` in `plan.md` and Reads each card by range; it never reads the whole plan |

## Order
| ID | Step |
|---|---|
| E03 | Baseline: the main runs `scripts/gates.sh baseline <slug>` before wave 1 (in C2, C3, C6 before the task). It records today's failures; at the end (E18) only new failures count. Without it, `scripts/gates.sh close` fails with "baseline missing" |
| E04 | Waves (the single home of the width): the docs agent writes the wave table (the `WAVE n:` lines of `gate.py --step plan`) and the plan path into `state.md`; a fresh session without it runs `gate.py --step plan` once. At most 4 executors per wave, dispatched in one message in the background; no polling, the returns arrive by themselves. Before each wave the main records `git rev-parse HEAD` as the base of the review range. Dispatch by agent type `prd-flow-executor`, the prompt carrying the slug, the state folder, the interpreter and the task card (at most 25 lines); the model is the one the card marks. A failed task reruns alone. On rate limits the wave shrinks to 2. A big file has a serial chain |
| E22 | Isolation only when needed: a worktree per executor only when parallel tasks of a wave share build or test state that interferes; otherwise one tree with disjoint Owns |
| E05 | Each return: check only `git diff --stat` against the file list the executor returned (the reviewer reads content), and commit those files with the message the executor proposed. A gap that is a rule or contract divergence goes to the short C5 (R09, E08 to E10); only a missing technical detail becomes a question to the user or a new task, resolved before the task that depends on it. The message carries the `Rules:` or `Case: none (...)` trailer |
| E06 | Every wave gets one review by the `prd-flow-reviewer` on the combined wave diff (a one-task wave included); rounds, cap and severities: `.claude/skills/prd-flow/reference/review.md`. Fixes go to a `prd-flow-executor` with the finding IDs |
| E07 | An agent is never resumed: continuing its work is a new agent with the pack, the state files and a handoff when needed. An agent the user interrupted: first save what it left with `git --no-pager diff` into a patch in `state/<slug>/` |

## Rule change in the middle of execution (short C5, R09)
The trigger and the stop are R09 (SKILL.md).

| ID | Step |
|---|---|
| E08 | Stop the tasks that touch the behavior (review.md V06) and dispatch the `prd-flow-surveyor` in short mode: K01, K02, K11, K12 on the touched rules only, confrontation of at most 15 lines in product language (R07). It appends a dated scaffold to `interview.md` (`## Dimensions (YYYY-MM-DD)`, only the reopened dimensions) and to `approved-rules.md` (`## YYYY-MM-DD`); it never rewrites `state.md` nor resets the review counter. Outside a C5 (during C2, C3 or C6; the prompt says `Case short C5 outside a C5`) the surveyor creates the files instead: `interview.md` (first line `Scope: short C5 outside a C5`; without it the gate requires D01 to D15), `approved-rules.md` and `changes/NNN-<slug>/decisions.md`. The main creates no file by hand. Show the current rule and the proposal and ask. More than one rule, or a dimension the original change never covered: re-enter as a full C5 |
| E09 | Interview of the reopened dimensions only: the main fills the dated table with its own `Confirmed:` line (at least one dimension), and adds `DEC-` rows to `decisions.md` |
| E10 | Approved: the main edits the rows of the dated section (`### <prd file>.md` and its rows; a re-approved ID replaces its earlier row, the gate takes the latest; old text literal for the CHANGELOG), runs `gate.py --rules`, and dispatches the `prd-flow-docs` agent in `short <YYYY-MM-DD>` mode (`--applied` green), then TRD, and the plan only gets the new tasks appended (outside a C5 the docs agent creates `plan.md`); execution resumes. No hand edits of PRD, HTML or CHANGELOG. The review counter does not reset without explicit approval |

## Cost per agent
The weight of an agent is the context it resends on every call, times the number of calls. An executor with 300k tokens and 150 calls costs more than the rest of the route.

| ID | Rule |
|---|---|
| E12 | No agent opens a subagent. Parallelism belongs only to the main thread, by wave |
| E13 | Executor and fixer run on `sonnet`. `opus` only when the plan marks the task as a new safety decision (or another reason written on the task line) |
| E14 | An agent that hit its ceiling (`reference/review.md` V08), or passed about 150k tokens, is replaced by a new agent with a handoff of at most 10 lines (files touched, red tests, next step). At most 2 reruns per step; the third failure becomes a gap that returns the ERROR lines |
| E15 | The agent prompt names the task's files, entry symbols and tests (its card); it does not reread the whole plan, only its section |
| E16 | Tests run with output redirected to a file, and only the `FAILED` and `ERROR` lines and the summary come back into context |
| E17 | Brake: an agent that hits its ceiling twice, or a wave that takes more than twice the time of the previous one, stops the execution and goes to the user with what is left and the cost so far. Never run for hours without reporting |
| E18 | **Tests only at the end.** During execution no agent runs the full suite: the executor runs only the tests related to what it touched, the mirror file and those that import or use the touched module (`Grep` of the module path in the test folders), with the single-file command of `repo.md` (no coverage). A failure in a test unrelated to what it touched is not investigated midway: it waits for the end. The full suite runs a single time, after all tasks are applied; then a closing task fixes the tests and the code that are wrong according to the PRD |
| E19 | **Moving code is done by script.** In a refactor the agent decides the map (which symbol goes to which module) and a script cuts and pastes the blocks by line range or AST; the model only fixes imports and calls. Never retype a function body: it is slow and creates transcription errors. With huge test files, split code and tests first and prove statically (import check, type check, lint); run tests in parts afterwards |
| E20 | **Closing.** After the last wave and its review: run `promote.py <slug>` (drops markers, fills Source, writes the CHANGELOG, rebuilds the HTML, archives the change folder; it leaves the state in place). Its warnings (an amendment fold it cannot decide, the `design.md` destinations of a size L) go to a `prd-flow-docs` dispatch in `fold` mode, never to the main. Commit the results, then `scripts/gates.sh close <slug>` (full suite against the baseline, lint, trailers, `gate.py --final`, retro); when it passes it clears the state folder of the slug and the `_gate`, `_tests` and `_close` folders. C2, C3 and C6 have no promote: baseline before the task, `scripts/gates.sh close <slug>` after it. The final report lists each retro finding (severity, value, threshold, evidence) or says the run stayed within every threshold; findings become tasks only when the user asks. The recording is silent and no agent turns it on or off |

## Deliveries and cost record
| ID | Rule |
|---|---|
| E21 | `deliveries.md` is always at `.claude/prd-flow/state/<slug>/deliveries.md`: one block per finished task (at most 8 lines: what was created, the symbols later tasks consume, the `Source:` files). Each `Source:` line reads `Source: <ID> <path[::symbol]>`, one per rule ID, and `promote.py` reads exactly these to fill the PRD Source column (no line: the rule stays planned and is listed). A consumer reads the producer's block, never its code |
| E11 | At the end of each wave, append one line to `state.md`: wave, agents dispatched, review rounds, the most expensive agent (tokens and minutes). It is the baseline to compare one execution with the next |

```markdown
## Cost (E11)
| Wave | Agents | Reviews | Most expensive |
|---|---|---|---|
| 1-A | 6 | 1/5 | T04 · 120k tokens · 9 min |
```

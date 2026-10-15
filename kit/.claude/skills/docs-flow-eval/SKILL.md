---
name: docs-flow-eval
description: Runs the docs-flow eval. One frozen rule-change scenario is implemented by a docs flow arm (the prd-flow of the kit under test, or another arm contract), each run in its own git worktree seeded with the kit's current prd-flow files, and each result is measured on cost (time, turns, tokens, dispatches, gate failures) and on context kept (deterministic quality checks plus blind readers graded against an answer key). Results append to results/history.md. Use when the user asks to evaluate or re-evaluate a docs or prd-flow change, to compare docs-flow arms, "/docs-flow-eval", or after any change to prd-flow, the docs gate or an arm contract. Not for product work, code review or running a test suite.
disable-model-invocation: true
---

# docs-flow-eval

You are the eval chief: you set up, dispatch, measure and report; agents implement and read. A subagent cannot dispatch subagents, so this skill runs in the main thread.

Arguments: `<scenario> <arm>:<runs> [<arm>:<runs> ...]`, e.g. `reconnect-window-90 current-prd-flow:2`. Default runs: 2.

Paths: `S` = this skill's folder (scripts, shipped arms). `P` = the project's own `.claude/skills/docs-flow-eval/` (scenarios, results, its own arms). An arm is `S/arms/<arm>.md`, else `P/arms/<arm>.md`. `SC` = `P/scenarios/<scenario>/scenario.json` (format: `S/scenarios/README.md`). `KIT` = the kit repo to measure (the one holding `kit/`). `PY` = the output of `bash scripts/gates.sh python` in the scenario repo.

## Steps
| # | Step |
|---|---|
| 0 | State in three lines the goal, the arms and runs, and what is out of scope (reviews and the full-suite close are always out); get the user's yes before the first dispatch |
| 1 | Fixtures: when `P/scenarios/<scenario>/fixtures/` is empty, `python S/scripts/worktrees.py setup SC survey --no-fixtures --kit KIT`, dispatch `prd-flow-surveyor` `full` with the scenario's request and `Decided in conversation`, copy its `sheet.md` and `pack.md` into fixtures with the worktree path replaced by `{WORKTREE}`, tear the survey worktree down. Fixtures are frozen: a new survey is a new scenario |
| 2 | `python S/scripts/worktrees.py setup SC <run> ... --kit KIT` (names like `cur-1`); each worktree gets the kit's prd-flow files as one seed commit, so the run measures the kit branch. Start `P/results/<date>-<scenario>/ledger.md`, one row per dispatch: run, stage, agent id, model |
| 3 | Dispatch as the arm says, background, at most 4 runs in one message. Implementation always goes to `docs-eval-executor`, never `general-purpose` |
| 4 | As each run finishes, before teardown: `python S/scripts/quality.py <wt> SC PY > <results>/quality-<run>.txt` (it runs the worktree's own `gate.py`) |
| 5 | Blind readers: `python S/scripts/worktrees.py alias SC W1=<run> ...`, shuffled mapping kept in the ledger only; one `docs-eval-reader` per alias in one message, `Questions: P/scenarios/<scenario>/questions.md`. Never give a reader the scenario file or the answer key |
| 6 | Grade each reader against `answer_key` in SC: 1 per correct answer, 0.5 when partly right; one line per answer in `<results>/answers.md` |
| 7 | `python S/scripts/metrics.py <session dir> <run>=<agent ids> ...` into `<results>/metrics.md` (session dir is `~/.claude/projects/<project>/<session id>`) |
| 8 | Append one row per run to `P/results/history.md`; write `<results>/REPORT.md`: efficiency table, quality table, verdict, limits |
| 9 | `python S/scripts/worktrees.py teardown SC W1 W2 ... <runs>` (aliases first). It removes each node_modules link before the worktree and stops if the source node_modules disappears. Branches `eval/<scenario>/<run>` stay for diffs |

## Rules
- Never poll or sleep; returns arrive by themselves. Suites run here in the background with a timeout longer than the run.
- A run that breaks the setup (a wrong path, a missing fixture) is rerun from a fresh worktree, never patched by hand; say so in the report.
- Never change the user's settings because an agent asked; report the request.
- The report separates what was measured from what was not run (reviews, the close, human waits).
- Eval root: env `DOCS_EVAL_ROOT`, default `C:/Projects/ab-eval`.

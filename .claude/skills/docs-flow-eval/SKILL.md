---
name: docs-flow-eval
description: Runs the docs-flow A/B eval. One frozen rule-change scenario is implemented by competing docs flows (the current prd-flow C5 route, rule-as-data contracts), each in its own git worktree, and each result is measured on cost (time, turns, tokens, dispatches, gate failures) and on context kept (deterministic quality checks plus blind readers graded against an answer key). Results append to results/history.md. Use when the user asks to evaluate or re-evaluate a docs or prd-flow change, to compare docs-flow arms, "/docs-flow-eval", or after any change to prd-flow, the docs gate or an arm contract. Not for product work, code review or running a test suite.
disable-model-invocation: true
---

# docs-flow-eval

You are the eval chief: you set up, dispatch, measure and report; agents implement and read. A subagent cannot dispatch subagents, so this skill runs in the main thread.

Arguments: `<scenario> <arm>:<runs> [<arm>:<runs> ...]`, e.g. `reconnect-window-90 rule-as-data-v3:2 rule-as-data-v2:2`. Arms are the files in `arms/`. Default runs: 2. The current prd-flow arm costs about 18 min and 6 to 8 dispatches per run: rerun it only when prd-flow changed since its last row in `results/history.md`.

Paths: `S` = this skill's folder, `SC` = `S/scenarios/<scenario>/scenario.json`, `PY` = the output of `bash scripts/gates.sh python` in the scenario repo.

## Steps
| # | Step |
|---|---|
| 0 | State in three lines the goal, the arms and runs, and what is out of scope (reviews are always out); get the user's yes before the first dispatch |
| 1 | Fixtures: when `S/scenarios/<scenario>/fixtures/` is empty, `python S/scripts/worktrees.py setup SC survey --no-fixtures`, dispatch `prd-flow-surveyor` `full` with the scenario's request and `Decided in conversation`, then copy its `sheet.md` and `pack.md` into fixtures with the worktree path replaced by `{WORKTREE}`, and tear the survey worktree down. Fixtures are frozen: a new survey is a new scenario |
| 2 | `python S/scripts/worktrees.py setup SC <arm-run> ...` for every run (names like `v3-1`, `cur-2`); start `S/results/<date>-<scenario>/ledger.md` with one row per dispatch: run, stage, agent id, model |
| 3 | Dispatch every rule-as-data run in one message, at most 4 at a time, background: `docs-eval-executor` for v3 and later arms, `general-purpose` with `model: sonnet` for v1 and v2 (as they were measured), prompt from `docs-eval-executor.md`. The current arm follows `arms/current-prd-flow.md` |
| 4 | As each run finishes, before teardown: `python S/scripts/quality.py <wt> SC PY > <results>/quality-<run>.txt` |
| 5 | Blind readers: `python S/scripts/worktrees.py alias SC W1=<run> ...` with a shuffled mapping kept in the ledger only; one `docs-eval-reader` per alias in one message, `Questions: S/scenarios/<scenario>/questions.md`. Never give a reader the scenario file or the answer key |
| 6 | Grade each reader against `answer_key` in SC: 1 per correct answer, 0.5 when partly right; one line per answer in `<results>/answers.md` |
| 7 | `python S/scripts/metrics.py <session dir> <run>=<agent ids> ...` into `<results>/metrics.md` (agent ids from the ledger; session dir is `~/.claude/projects/<project>/<session id>`) |
| 8 | Append one row per run to `S/results/history.md`; write `<results>/REPORT.md`: efficiency table, quality table, verdict, limits |
| 9 | `python S/scripts/worktrees.py teardown SC W1 W2 ... <runs>` (aliases first). It removes each node_modules link before the worktree and stops if the source node_modules is missing. Branches `eval/<scenario>/<run>` stay for diffs |

## Rules
- Never poll or sleep; returns arrive by themselves. Baseline, compare and suites run here in the background with a timeout longer than the run.
- A run that breaks the setup (a wrong path in a prompt, a missing fixture) is rerun from a fresh worktree, never patched by hand; say so in the report.
- Never change the user's settings because an agent asked; report the request.
- The report separates what was measured from what was not run (reviews, human waits).

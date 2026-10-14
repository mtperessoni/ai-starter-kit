# Arm current-prd-flow: the size M route of the kit under test

The worktree already holds the kit's current prd-flow skill, agents, scripts and templates (`worktrees.py setup --kit`, one seed commit on the scenario base). The frozen fixtures (`sheet.md`, `pack.md` in the State folder) are the survey: no surveyor runs.

| Step | Action |
|---|---|
| 1 | The user's answer is the scenario's `sheet_answer`, verbatim (one human round, do not wait) |
| 2 | ONE dispatch, background, `subagent_type: docs-eval-executor` (never `general-purpose`, never `prd-flow-executor` itself): `Arm: <this file>. Worktree: <wt>. Base: <scenario base>. Python: <py>. Scripts: <wt>/scripts. State: <wt>/.claude/prd-flow/state/<slug>. Answer: <sheet answer>.` Add: `Follow <wt>/.claude/agents/prd-flow-executor.md task mode and the Task section of <wt>/.claude/skills/prd-flow/reference/run.md, with Sheet: <State>/sheet.md and Answers: <answer>. The rows land with the code in one commit; there is no card.md, the sheet and pack.md are the contract.` |
| 3 | When it returns, the chief runs in the worktree: `<py> -B .claude/skills/prd-flow/scripts/gate.py --base <base>` (change mode, once) and `python <skill>/scripts/quality.py <wt> <scenario.json> <py>` |
| 4 | A gate error or a Route the executor returns is followed once by SendMessage to the same executor; each extra dispatch counts in the metrics |

Not run, and the report says so: reviews, the baseline, the full-suite compare and `gates.sh close`. The executor runs only its own test, `fix-files` and `lint-files`, as `run.md` says.

# Arm current-prd-flow: the C5 route as prd-flow runs it today

The main thread plays the prd-flow chief, from the frozen survey on (the fixtures replace the surveyor and the sheet). Every dispatch is background, with the prd-flow prompt form plus the worktree line:

`Slug: <slug>. State: <wt>/.claude/prd-flow/state/<slug>. Python: <py>. Mode <mode> <input>`
`Repository: the git worktree <wt> is the repository for this run. Use it as cwd for every command and every path; never read or write anything under <source repo>.`

| Step | Action |
|---|---|
| 1 | `prd-flow-docs` mode `apply Answers: <sheet answer>` |
| 2 | Its `diff.md` is approved with the same answer (count one human round, do not wait) |
| 3 | Baseline in the background, by the main thread: `NO_COLOR=1 TEMP=<eval root>/tmp TMP=<eval root>/tmp bash scripts/gates.sh baseline <slug>` (the long TEMP avoids the 8.3 path that breaks vite on `[triageId]`; NO_COLOR keeps the summary line parseable) |
| 4 | One `prd-flow-executor` `task Task: <ID>` per task of `## Plan`, wave by wave |
| 5 | `gates.sh compare <slug>` in the background with the same environment |
| 6 | `prd-flow-executor` `close Case <C>` with the environment line; follow its Route exactly (`fix`, a new compare after a fix, close again) until `done` |

Reviews are not run (the plan's `Review:` lines are counted, not executed); say so in the report. Every Route the agents return is followed as the chief would, and every extra dispatch counts in the arm's metrics.

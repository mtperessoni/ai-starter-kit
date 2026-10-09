# Dispatch (the chief's prompts, resume, ledger, cross-repo)

Read once by the chief at the start of a run, with `repo.md`: the only reference the chief reads.

## Prompt
One line per dispatch, `subagent_type: prd-flow-<role>` (never `general-purpose`):

`Repo: <alias>. Slug: <slug>. State: <cwd>/.claude/prd-flow/state/<slug>. Python: <interpreter>. Mode <mode>. <task line or handoff>`

| Part | Rule |
|---|---|
| `Repo:` | Alias from `.ai-kit/repos.json`; omitted in a single-repo run (DP10) |
| `Python:` | The output of `scripts/gates.sh python`: the only interpreter a prompt names |
| Mode | surveyor `query\|light\|full\|short`; executor `task\|fix\|close`; reviewer `review\|recheck`; recheck `recheck`; docs `apply\|apply merge\|adjust\|short\|plan\|c4\|fold\|context` |
| Model | `model: sonnet` for the surveyor in `query` and `light`; every other dispatch keeps the agent's default |
| Background | `run_in_background: true` on every dispatch (DP02) |

| Role | Task line |
|---|---|
| surveyor | `case <C1 to C6\|unclear> · size <M\|L\|unclear> · request: <words>`; `full` adds `Decided in conversation: "<verbatim>"` and `Preferences: "<verbatim>"`; `short` adds `Touched: <behavior, task, files>` and `outside a C5` when no C5 runs |
| executor | `Task: <ID>` or `Card: <state>/card.md`; `fix` the handoff from the Route; `close` `Case <C>` |
| reviewer | `Round N/5. Wave: <n\|last>. Commits: <hashes>. Verify: <log path>` |
| recheck | `Round N/5. Commits: <fix hashes>. Findings: <lines, or the findings file>`; to the warm reviewer by SendMessage as `Mode recheck. ...`, else to `prd-flow-recheck` |
| docs | `apply Answers: <verbatim>`, then `Answers 2: <verbatim>`; `short <YYYY-MM-DD> Answers: <verbatim>`; `adjust: <words>`; `apply merge`, `plan`, `c4`, `fold`, `context` with the Route's handoff |

The prompt names the task, never the plan: each agent reads its own card.

## Rules
| ID | Rule |
|---|---|
| DP01 | **Premise.** A prompt carries no domain assumption: the request in the user's words, rule IDs, paths and answers verbatim, never the chief's reading. The user's own words go verbatim, with the scope they covered: `Decided in conversation:` and `Preferences:` become assumed lines on the sheet |
| DP02 | **Background and parallel.** Only the chief runs anything in the background. A whole wave goes in one message (its width comes from the gate's wave table, at most 4; on rate limits 2), and so do independent docs, review and fix dispatches with disjoint files. A failed task reruns alone. Never poll, never wait on one agent while independent work exists: returns arrive by themselves |
| DP03 | **Resume or replace.** An agent that holds the context, is under about 150k tokens and below its ceiling (`run.md` V08) is continued with SendMessage: a fix goes to the warm executor of the task with the finding lines on its Owns, and the recheck to the warm reviewer of the round. Otherwise a new dispatch of the same role with a handoff of at most 10 lines. A plan correction is one docs `adjust: <words>`, never a revert and a redo. After the plan is approved the chief may offer execution in a fresh session on the fast model: `## Plan` alone drives it |
| DP04 | **Ledger.** `## Chief` keeps one line per dispatch, `role · mode · task · agent id · status` (`running`, `done`, `failed`; the repo in a cross-repo run). Before dispatching, check it: the same role, mode and task `running` or `done` is not dispatched again |
| DP05 | **Follow-up.** A user correction is never a new survey: it is the one `sheet-2.md` or docs `adjust` |
| DP06 | **Baseline.** `scripts/gates.sh baseline <slug>` as a background Bash in the target repo (its path as cwd in a cross-repo run), never inside an agent, never `--bg`. After the plan commit in C5 and after the card in C2, C3, C6 (after the docs `plan` commit when the surveyor returned `Route: docs plan`); not for C4. Executors never wait for it. Close reads its status once; `close` fails with "baseline missing" when it never started |
| DP07 | **Wave watch and verification.** `scripts/gates.sh watch <slug>` starts in the same message as the wave dispatch and tracks agents started in the last 30 min (`--since <epoch>` exists; not needed). Exit lines: `done: no agent running` (go on: reap, then verify below); `stuck: <agent id> <atype> idle <n> min (a silent long command is possible)` and `deadline: <ids>` (TaskStop those agents, `gates.sh reap`, redispatch with `Interrupted: yes`); `unknown: no events file` or `unknown: no SubagentStart seen in the events file` (telemetry is off: wait for the returns as before and say so in the final report). At a wave end: `scripts/gates.sh reap`, then ONE background `scripts/gates.sh verify <slug>` (related tests of every file changed in the wave, structure tests, docs gates) with the wave reviewer. Verify failures and findings go to the same fix: the reviewer copies the failure lines it maps to a card, with their `Task:`, into its `Route: executor fix`, and the chief sends each task's lines to that task's warm executor (DP03), the `Task: none` lines to one new executor `fix`; the next verify reruns only what failed. During the last review also a background `scripts/gates.sh compare <slug>`; executor `close` reuses both |
| DP08 | **Docs gates.** Stdout is errors plus `warnings: N (see <file>)`; warnings are reminders read in that file only to decide on one; a gate runs once per phase, never in a loop. One call: `scripts/gates.sh docs <slug>`; final: `gate.py --final --change <slug>`; at classification the surveyor runs `gate.py --snapshot <slug>` so older drift is not blamed on the change |
| DP09 | **Hold.** Close runs `promote.py --hold <ID> --reason <words>` for a row blocked by an eval, a deploy or another repository; it stays `planned` and is listed in the close return |

## Cross-repo
| ID | Rule |
|---|---|
| DP10 | `.ai-kit/repos.json` lists each repository: `alias`, `path`, `adapter`, `interpreter`. The chief is started in the target repository (or its worktree) and prefixes every prompt with `Repo: <alias>`; the agent works with that path as cwd and that interpreter |
| DP11 | State and telemetry are per repository: `<repo path>/.claude/prd-flow/state/<slug>` and that repository's `.ai-kit/runs/` |
| DP12 | Dispatches to different repositories run in parallel; inside one repository only with disjoint Owns, in one tree. A worktree per executor only when parallel tasks share build or test state that interferes |
| DP13 | A prompt to another repository follows DP01: the request and the approved rows, nothing else; it never tells an agent to follow another agent's file |

## Records in `## Chief`
```markdown
Ledger:
- surveyor · full · survey · a1b2 · done
- executor · task · T01 · c3d4 · running
review: 2/5
- wave 1 · round 1 · 0 Critical, 3 High · fix
- wave 1 · round 2 · 0 Critical, 0 High, 1 Medium · closed
Pending: CS-004 Medium (wave 1)
Wave time: wave 1 12 min
```

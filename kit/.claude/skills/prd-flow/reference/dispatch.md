# Dispatch (the chief's prompts, resume, cross-repo)

Read once by the chief at the start of a run, with `repo.md`: the only reference the chief reads.

## Prompt
One line per dispatch, `subagent_type: prd-flow-<role>`. Implementation is always dispatched to `prd-flow-executor`, never `general-purpose`:

`Repo: <alias>. Slug: <slug>. State: <cwd>/.claude/prd-flow/state/<slug>. Python: <interpreter>. Mode <mode>. <task line or handoff>`

| Part | Rule |
|---|---|
| `Repo:` | Alias from `.ai-kit/repos.json`; omitted in a single-repo run (DP10) |
| `Python:` | The output of `scripts/gates.sh python`, run once by the chief: the only interpreter a prompt names |
| Mode | surveyor `full\|short` (rule changes only); executor `task\|fix\|close`; reviewer `review\|recheck`; recheck `recheck`; docs `plan\|adjust\|c4` (size L and a stale PRD only; never for size S or M) |
| Model | Every dispatch passes `model`: sonnet, or opus with a one-line reason (the surveyor in `full` and `short`) |
| Background | `run_in_background: true` on every dispatch (DP02) |

| Role | Task line |
|---|---|
| surveyor | `case C5 · size <M\|L\|unclear> · request: <words>`; `full` adds `Decided in conversation: "<verbatim>"` and `Preferences: "<verbatim>"`; `short` adds `Touched: <behavior, task, files>` and `outside a C5` when no C5 runs |
| executor | `Task: <one line: goal, rule IDs, paths to read, paths owned>` (size L: `Plan: <path>` and the task ID), a rule change adding `Sheet: <state>/sheet.md` and `Answers: <verbatim>`; `fix` the handoff from the Route; `close` `Case <C>` (it runs `gates.sh close <slug> --case <C>`; a rerun after a logged `closed: <commit>` is answered from its earlier return) |
| reviewer | `Round N/5. Wave: <n\|last>. Commits: <hashes>` |
| recheck | `Round N/5. Commits: <fix hashes>. Findings: <lines, or the findings file>`; to the warm reviewer by SendMessage as `Mode recheck. ...`, else to `prd-flow-recheck` |
| docs | `plan Answers: <verbatim>` (size L), then `Answers 2: <verbatim>`; `adjust: <words>` (also the reply to `sheet-short-<k>.md` when a plan exists); `plan: <request, rule IDs, areas>` over several tasks of C2, C3, C6; `c4: <the divergence in words>` |

A task is one line; the prompt names the task, never the plan: each agent reads its own task line.

## Rules
| ID | Rule |
|---|---|
| DP01 | **Premise.** A prompt carries no domain assumption: the request in the user's words, rule IDs, paths and answers verbatim, never the chief's reading. The user's own words go verbatim, with the scope they covered: `Decided in conversation:` and `Preferences:` become assumed lines on the sheet |
| DP02 | **Background and parallel.** Only the chief runs anything in the background. A whole wave goes in one message (its width comes from the gate's wave table, at most 4; on rate limits 2), and so do independent docs, review and fix dispatches with disjoint files. A failed task reruns alone. Never poll, never wait on one agent while independent work exists: returns arrive by themselves |
| DP03 | **Resume or replace.** An agent that holds the context, is under about 150k tokens and below its ceiling (`run.md` V08) is continued with SendMessage: a fix goes to the warm executor of the task with the finding lines on its Owns, and the recheck to the warm reviewer of the round. Otherwise a new dispatch of the same role with a handoff of at most 10 lines. A plan correction is one docs `adjust: <words>`, never a revert and a redo |
| DP05 | **Follow-up.** A user correction is never a new survey: it is the one `sheet-2.md` or docs `adjust` |
| DP06 | **Baseline.** `scripts/gates.sh baseline <slug>` as a background Bash in the target repo (its path as cwd in a cross-repo run), never inside an agent, never `--bg`. After the sheet reply in C5 (after the docs `plan` commit in size L) and after the task line in C2, C3, C6 (after the docs `plan` commit when several tasks need a plan); C4 needs none (its close skips baseline and compare). Executors never wait for it. Close reads its status once; without it `close` fails with "baseline missing" in C2, C3, C5, C6, and a baseline taken at close would hide the change's own failures |
| DP07 | **Wave and verification.** An agent that returns nothing past its ceiling is stopped with TaskStop, `gates.sh reap` runs, and the task is redispatched with `Interrupted: yes`. At a wave end: `scripts/gates.sh reap` as its own Bash call; in the next message ONE background `scripts/gates.sh verify <slug>` (related tests of every file changed in the wave, structure tests, docs gates) with the wave reviewer, which never reads it. Findings and verify failures go to one fix: each task's finding lines to that task's warm executor (DP03), the `Task: none` lines and the verify failure lines to one new executor `fix`; the next verify reruns only what failed. During the last review also a background `scripts/gates.sh compare <slug>`; after the last fix restart it (a fix changes the tree). Close reads that result: "compare is still running": wait for its event; "no compare result": start `compare`; then rerun close |
| DP08 | **Docs gates.** Stdout is errors plus `warnings: N (see <file>)`; warnings are reminders read in that file only to decide on one; a gate runs once per phase, never in a loop. One call: `scripts/gates.sh docs <slug>` |
| DP09 | **Hold.** A rule blocked by an eval, a deploy or another repository is listed in the close return with its reason; it is never written as a pending marker (D4). Size L close may use `promote.py --hold <ID> --reason <words>` for an existing frozen marker |

## Cross-repo
| ID | Rule |
|---|---|
| DP10 | `.ai-kit/repos.json` lists each repository: `alias`, `path`, `adapter`, `interpreter`. The chief is started in the target repository (or its worktree) and prefixes every prompt with `Repo: <alias>`; the agent works with that path as cwd and that interpreter |
| DP11 | State and telemetry are per repository: `<repo path>/.claude/prd-flow/state/<slug>` and that repository's `.ai-kit/runs/` |
| DP12 | Dispatches to different repositories run in parallel; inside one repository only with disjoint Owns, in one tree. A worktree per executor only when parallel tasks share build or test state that interferes |
| DP13 | A prompt to another repository follows DP01: the request and the approved rows, nothing else; it never tells an agent to follow another agent's file |

## Records in `## Chief`
```markdown
review: 2/5
- wave 1 · round 1 · 0 Critical, 3 High · fix
- wave 1 · round 2 · 0 Critical, 0 High, 1 Medium · closed
Pending: CS-004 Medium (wave 1)
```

# Dispatch (the chief's prompts, background, resume, cross-repo)

Read once by the chief at the start of a run, with `repo.md`; it is the only reference the chief reads. The chief never reads the plan or a diff, and reads only the PRD rows a sheet cites.
## Prompt template
Short form, one line per dispatch:

`Repo: <alias>. Slug: <slug>. State: <cwd>/.claude/prd-flow/state/<slug>. Mode <mode>. <task line or handoff>`

| Part | Rule |
|---|---|
| `Repo:` | Alias from `.ai-kit/repos.json`; omitted in a single-repo run (DP10) |
| `Python:` | The output of `scripts/gates.sh python`, run by the chief (its one extra Bash call) and added to every prompt; the only interpreter any prompt names |
| Mode | surveyor `query\|light\|full\|short`; executor `task\|fix\|close`; reviewer `review`; recheck `recheck`; docs `apply\|apply merge\|adjust\|c4\|fold\|context` |
| Agent | `prd-flow-<role>`, else `general-purpose` following its `.claude/agents` file |

Task lines:
| Role | Task line |
|---|---|
| surveyor | `case <C1 to C6\|unclear> · size <M\|L\|unclear> · request: <words>`; `full` adds `Decided in conversation: "<verbatim>"` and `Preferences: "<verbatim>"`; `short` adds `Touched: <behavior, task, files>` and, outside a C5, `outside a C5` |
| executor | `Task: <ID>` or `Card: <state>/card.md`; `fix` carries the finding lines; `close` carries `Case <C>` and runs `gates.sh close <slug> --case <C>` (a rerun after a logged `closed: <commit>` is answered from its earlier return) |
| reviewer | `Round N/5. Wave: <n\|last>. Commits: <hashes>` |
| recheck | `Round N/5. Commits: <hashes>. Findings:` <lines or `findings-r<N>.md`> |
| docs | `apply` `Answers: <verbatim>`, then `Answers 2: <verbatim>` for the follow-up sheet; `Case short` when the sheet is a `sheet-short-<k>.md` (also outside a C5); `apply merge` after the `context` fan-out (the handoff names the facts file); `adjust: <words>` |

## Rules
| ID | Rule |
|---|---|
| DP01 | **Premise.** A prompt carries no domain assumption: the request in the user's words, rule IDs, paths and answers verbatim, never the chief's reading of the domain. The user's own words are allowed verbatim, with the scope they covered: `Decided in conversation:` and `Preferences:` become Assumed lines on the sheet, never a label on the chief's summary. A prompt to another repository names only the request and the approved rows |
| DP02 | **Background and parallel by default.** Every dispatch runs in the background. A whole wave goes in one message; so do independent docs, review and fix dispatches with disjoint files. The chief never waits on one agent while other independent work exists, and never polls: returns arrive by themselves |
| DP03 | **Resume or replace.** A warm agent that already holds the context, is under about 150k tokens and did not hit its ceiling (review.md V08) is continued with SendMessage; otherwise a new dispatch of the same role with a handoff of at most 10 lines. A correction to a plan is one in-place docs `adjust: <words>`, not a revert and a redo |
| DP04 | **Ledger.** `## Chief` keeps a dispatch ledger, one line per dispatch: `role · mode · task · agent id · status` (`running`, `done`, `failed`). Before dispatching, the chief checks it: an entry for the same role, mode and task that is `running` or `done` is not dispatched again; the chief waits for or uses that return |
| DP05 | **Follow-up.** A user correction is never a new survey: it is the one follow-up sheet (`sheet-2.md`) or docs `adjust` |
| DP06 | **Baseline.** The chief runs `scripts/gates.sh baseline <slug>` as a background Bash in the TARGET repo (a cross-repo run: that repo's path as cwd), never inside another agent, so the harness sends a completion event: no detached `--bg`, no waiting loop. Start it after the plan commit in C5 and after the surveyor card in C2, C3 and C6; C4 needs none (its close skips baseline and compare). Executors do not wait for it. Close reads the baseline status file once and never polls; without a baseline `close` fails with "baseline missing" in C2, C3, C5, C6, and a baseline taken at close would hide the change's own failures |
| DP07 | **Wave verification.** When a wave ends the chief runs `scripts/gates.sh reap` as its own Bash call; in the next message it starts ONE background `scripts/gates.sh verify <slug>` (related tests of every file changed in the wave, structure tests, docs gates; output to a file) together with the wave reviewer. The reviewer and recheck do not read the verify output (it runs beside them); the chief routes verification failures together with the review findings into ONE `fix` dispatch; the next verification reruns only what failed. During the last review the chief also starts `scripts/gates.sh compare <slug>` in the background; after the last fix it restarts `compare` (a fix changes the tree, so the earlier result does not apply). Close reads that result: "compare is still running": wait for its event; "no compare result": start `compare`; then rerun close |
| DP08 | **Docs gates.** Reminders, not locks: the plan alignment (`Reached from:`), sheet lint and shared-file owner checks print warnings the agent reads and decides on; none blocks, and each gate runs once per phase, never in a loop. One call: `scripts/gates.sh docs <slug>` (rules, prd, trd, plan, applied). The final gate is `gate.py --final --change <slug>`; at classification the surveyor runs `gate.py --snapshot <slug>` so older drift is not blamed on the change |
| DP09 | **Hold.** Close promotes with `promote.py --hold <ID> --reason <words>` for a row blocked by an eval, a deploy or another repository; it stays `planned` and is listed in the close return |

## Behavior by role
No agent has a power limit; these are behavior rules. The agent files hold the detail.

| ID | Role | Behavior |
|---|---|---|
| BR01 | chief | Splits work into one-concern tasks; sends independent work in parallel; resumes warm agents (DP03); puts no assumption of its own in a prompt (DP01) |
| BR02 | surveyor | Reads the glossary, the section intros and the journey first; asks only what the PRD does not answer, on one sheet; plain words |
| BR03 | docs | Writes everything first, then runs `gates.sh docs` once and fixes what it flags |
| BR04 | executor | As its agent file `prd-flow-executor.md` says |
| BR05 | wave verification | One background run per wave end (DP07); the next reruns only what failed |
| BR06 | reviewer | Reads the executors' Self-check first, then the diff; findings only |
| BR07 | fix | One dispatch per wave takes the verification failures and the findings together; same Owns rules as an executor |

## Cross-repo mode
| ID | Rule |
|---|---|
| DP10 | `.ai-kit/repos.json` lists each repository: `alias`, `path`, `adapter`, `interpreter`. With it the chief prefixes every prompt with `Repo: <alias>`; the agent works with that path as its cwd and that interpreter |
| DP11 | State and telemetry are per repository: `<repo path>/.claude/prd-flow/state/<slug>` and that repository's `.ai-kit/runs/`. The `## Chief` ledger names the repo of each dispatch |
| DP12 | Parallel safety and the unit-only test rule live in the agent files, not in the prompts. Dispatches to different repositories run in parallel (DP02); inside one repository, only with disjoint Owns |
| DP13 | A prompt to another repository follows DP01: the request and the approved rows, nothing else |

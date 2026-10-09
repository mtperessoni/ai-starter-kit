# Dispatch (the chief's prompts, background, resume, cross-repo)

Read once by the chief at the start of a run, with `repo.md`; it is the only reference the chief reads. The chief never reads the plan, a diff or a PRD row. Rule IDs (`rules/`): DP01 WF65, DP02 SA54, DP03 SA48, DP04 SA50, DP05 WF71, DP06 TS43, DP07 TS50, DP08 WF73 and DS46, DP09 WF72, DP10 to DP13 SA55; round 0 is WF67.

## Prompt template
Short form, one line per dispatch:

`Repo: <alias>. Slug: <slug>. State: <cwd>/.claude/prd-flow/state/<slug>. Mode <mode>. <task line or handoff>`

| Part | Rule |
|---|---|
| `Repo:` | Alias from `.ai-kit/repos.json`; omitted in a single-repo run (DP10) |
| `Python:` | The interpreter from the first surveyor's `Survey` line, added to every later prompt; none for the first surveyor |
| Mode | surveyor `query\|light\|full\|short`; executor `task\|fix\|close`; reviewer `review`; recheck `recheck`; docs as returned |
| Agent | `prd-flow-<role>`, else `general-purpose` following its `.claude/agents` file |

Task lines:
| Role | Task line |
|---|---|
| surveyor | `case <C1 to C6\|unclear> · size <M\|L\|unclear> · request: <words>`; a delta re-survey (DP05) adds `Delta: <touched IDs and contexts>` |
| executor | `Task: <ID>` or `Card: <state>/card.md`; `fix` carries the finding lines; `close` carries `Case <C>` (a rerun after a logged `closed: <commit>` is answered from its earlier return) |
| reviewer | `Round N/5. Wave: <n\|last>. Commits: <hashes>` |
| recheck | `Round N/5. Commits: <hashes>. Findings:` <lines or `findings-r<N>.md`> |
| docs | `rules` `Answers:` <words>, plus `Confirmed: "<words>"` when the user already said it is clear; `prd-plan` `Answers:` <words> `Folded: yes` when folded; `trd-plan` `adjust: <words>` |

## Rules
| ID | Rule |
|---|---|
| DP01 | **Premise.** A prompt carries no domain assumption: the request in the user's words, rule IDs, paths and answers verbatim, never the chief's reading of the domain. "User-confirmed" is allowed only with the user's own words quoted and the scope they covered (this rule, this round); never as a label on the chief's summary. A prompt to another repository names only the request and the approved rows |
| DP02 | **Background and parallel by default.** Every dispatch runs in the background. A whole wave goes in one message; so do independent docs, review and fix dispatches with disjoint files. The chief never waits on one agent while other independent work exists, and never polls: returns arrive by themselves |
| DP03 | **Resume or replace.** A warm agent that already holds the context, is under about 150k tokens and did not hit its ceiling (review.md V08) is continued with SendMessage; otherwise a new dispatch of the same role with a handoff of at most 10 lines. A correction folded into a plan is one in-place docs `trd-plan` `adjust: <words>`, not a revert and a redo |
| DP04 | **Ledger.** `## Chief` keeps a dispatch ledger, one line per dispatch: `role · mode · task · agent id · status` (`running`, `done`, `failed`). Before dispatching, the chief checks it: an entry for the same role, mode and task that is `running` or `done` is not dispatched again; the chief waits for or uses that return |
| DP05 | **Delta re-survey.** After a user correction the surveyor re-checks only the touched rows and contexts, the same surveyor resumed (DP03) with `Delta:`; never a full survey again |
| DP06 | **Baseline.** Right after the plan commit the chief starts `scripts/gates.sh baseline <slug> --bg` itself, never inside another agent. Executors start without waiting for it. `scripts/gates.sh close` fails with "baseline missing" when it was never started |
| DP07 | **Full suite.** During the last review the chief starts `scripts/gates.sh compare <slug>` in the background; executor `close` reuses its result (execution.md E20) |
| DP08 | **Docs gates.** One call: `scripts/gates.sh docs <slug>` (rules, prd, trd, plan, applied). The final gate is `gate.py --final --change <slug>`; at classification the surveyor runs `gate.py --snapshot <slug>` so older drift is not blamed on the change |
| DP09 | **Hold.** Close promotes with `promote.py --hold <ID> --reason <words>` for a row blocked by an eval, a deploy or another repository; it stays `planned` and is listed in the close return |

## Cross-repo mode
| ID | Rule |
|---|---|
| DP10 | `.ai-kit/repos.json` lists each repository: `alias`, `path`, `adapter`, `interpreter`. With it the chief prefixes every prompt with `Repo: <alias>`; the agent works with that path as its cwd and that interpreter |
| DP11 | State and telemetry are per repository: `<repo path>/.claude/prd-flow/state/<slug>` and that repository's `.ai-kit/runs/`. The `## Chief` ledger names the repo of each dispatch |
| DP12 | Parallel safety and the unit-only test rule live in the agent files, not in the prompts. Dispatches to different repositories run in parallel (DP02); inside one repository, only with disjoint Owns |
| DP13 | A prompt to another repository follows DP01: the request and the approved rows, nothing else |

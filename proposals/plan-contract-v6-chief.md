# Contract v6: the orchestrator is the chief

Decided by the maintainer on 2026-10-08. The prd-flow main thread is a chief: it understands the request, talks to the user, dispatches agents, routes their returns and reports. It executes no task. Every interface below is shared by the parallel work; cite by ID (C6-NN); never ship these IDs in kit files.

## C6-01 Roles
| Role | Model | Does | Never |
|---|---|---|---|
| **chief** (the main thread) | the user's session | classify by the surveyor's return, ask the user, dispatch, route by return fields, keep the `## Chief` section of `state.md`, report | read PRD, TRD, source, diffs, references beyond its card, or any artifact other than `state.md` and `repo.md`; write any file other than `state.md` `## Chief`; run any script, gate, test or git command; fix, verify or redo an agent's work |
| **surveyor** (heavy) | strongest, high effort | every case starts here: proves the rules are functional (Source exists, has a caller outside tests, behavior matches the rule), sweeps conflicts and impact across every PRD, prepares the user's questions with scenarios and recommended options, writes the scaffolds; modes `query` (C1: the answer itself), `light` (C2, C3, C4, C6: rule rows, Source verdict, divergence, the task card), `full` (C5), `short` (mid-execution change) | write PRD, TRD or code |
| **docs** | strongest for plans, high effort | modes `rules` (writes `interview.md` answers and `approved-rules.md` from the answers the chief passes, runs `gate.py --rules` until green), `prd-plan` (PRD, TRD and plan in one dispatch; `trd-plan` is the adjustment and C2 mode), `fold`, `c4`, `context` (fan-out); reads `pack.md` only, never source | talk to the user |
| **executor** | fast | modes `task` (the card), `fix` (findings or a routed failure, with its own Owns and Read), `close` (runs `promote.py`, commits its output, runs `scripts/gates.sh close`, routes failures it cannot fix); commits its own work with the trailer; writes `deliveries/<task>.md` | change files outside Owns |
| **reviewer** | fast | one round per wave on the combined diff; the only reader of diffs | edit |
| **recheck** | cheapest | scoped check of a fix | edit |

## C6-02 Return contract (every agent, last lines of the return, nothing after)
```
Status: done | gap | blocked
Files: <paths written, or none>
Commit: <short hash, or none>
Route: none | user: <one question with options> | <role> <mode>: <handoff of at most 10 lines>
Next: <the step the chief runs next, in its own words>
```
At most 15 lines before these fields. The chief acts on the fields only: `done` and `Route: none` go to `Next`; `Route: user` becomes one AskUserQuestion; `Route: <role> <mode>` becomes that dispatch with the handoff as the prompt's task line. `gap` with no route is a contract breach: the chief re-dispatches the same role once with "return the Route field", then asks the user.

## C6-03 Failure routing (owner of every failure path)
| Failure | Owner |
|---|---|
| gate red after 2 reruns inside an agent | that agent returns `blocked` with `Route: <same role> <mode>` (a fresh agent with the error lines) or `user` when the rule is unclear |
| promote error: missing Source | executor `fix` (add the Source lines), then executor `close` again |
| promote error: superseded mismatch, fold needed | docs `fold`, then executor `close` |
| promote error: HTML build, archive, final gate | executor `fix` with the printed lines |
| close failure: tests, lint, trailers, G19 or G21 | executor `fix` with the printed lines, then executor `close` |
| close failure: missing baseline, a trailer that needs a history rewrite, drift that predates the change | `Route: user` from the executor (a baseline taken at close hides the change's own failures; a history rewrite is the user's call) |
| agent ceiling reached | the same role, new agent, the handoff from the return |
| review finding Critical or High | executor `fix`, then recheck; Medium and Low to the pending list in `state.md` |
| a High that may change a rule | `Route: user` from the reviewer; the chief asks; a rule change is the short C5 |
| invalid or missing return fields | C6-02 breach rule |

## C6-04 state.md sections (one writer each)
| Section | Writer | Content |
|---|---|---|
| `## Chief` | chief | case, size, slug, phase, the user's decisions log (one line each), review counter `review: N/5` with the last Critical plus High count, the wave's commit hashes, open finding lines, pending Medium and Low, `Next:` (enough for a resume to dispatch the reviewer or recheck) |
| `## Survey` | surveyor | contexts, conflicts, protected rules, the scaffold paths |
| `## Plan` | docs | plan path, one line per wave with task IDs, models and lens, a `Review:` line (per wave, or once after the last wave for a serial plan), `Execution:` line (baseline; per wave dispatch, review per the `Review:` line, recheck after a fix; close); the chief never opens the plan |
| `## Close` | executor `close` | promote result, written before the close gate (a passing close deletes the folder); the close summary and retro top findings travel in the return only |
Deliveries are per task: `.claude/prd-flow/state/<slug>/deliveries/<task>.md` (no shared file for parallel writers). Resume reads only `state.md`.

## C6-05 Artifacts complete for their consumer
| Artifact | Must contain so the consumer never explores |
|---|---|
| `pack.md` | literal rule rows, file and symbol map, conflicts, Leave items, DEC rows, contexts |
| task card | contract IDs, Owns, Read (exact paths or `path::symbol`), Decisions, Leave, Tests, Commit with trailer, Lens, Model |
| fix handoff | the finding or error lines, Owns, Read, the rule IDs; over 10 lines it points to a findings file the reviewer wrote in the state folder |
| close handoff | slug, the commands, what to commit |

## C6-06 Scripts are agents' tools
| Script | Kept because | Run by |
|---|---|---|
| `gate.py` (and modules) | deterministic validation of formats a model would check at many times the cost | surveyor, docs, executor `close`, CI |
| `build_prd_html.py` | deterministic page the maintainer reads | docs, executor `close` |
| `promote.py` | mechanical edits across PRD, CHANGELOG and archive | executor `close` only |
| `kit/scripts/close_gate.py` via `gates.sh close` | one call for every closing check | executor `close` only |
| kit tooling (`ratchet`, `related_tests`, `commit_trailers`, `retro`) | repository checks used by executors and CI | executors, CI |
No new script is added by this contract. A script error prints the owner and the next dispatch (C6-03) so the agent that ran it can route it.

## C6-07 Measurement (eval)
`main_violations` counts any chief tool use outside: Agent/Task dispatch, AskUserQuestion, Read or Write or Edit of `state.md`, Read of `repo.md`. Every Bash call by the chief is a violation (scripts, git, gates). Also: `return_compliance` (share of agent returns with the five fields), `surveyor_first` (the first dispatch of every run is the surveyor), the prompt and return sizes and the cache write at each agent start in `agents_report.py`.

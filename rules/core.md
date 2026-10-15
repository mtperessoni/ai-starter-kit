# Core rules (CR)

The rules that govern a delivery, in force from 2026-10-14. They replace the per-change duties of the eleven domain files, which stay in this folder as history and as the record of why each older rule existed. When a domain file and this file disagree, this file wins.

Why: in clara-ai change 013 (2026-10-14) the process was most of the work. 19 subagents and 2,724 tool calls ran 3 hours without a green suite or a PR; about 40% of the calls were reading and re-orienting, 13 files were edited by 3 or more agents, and every lane left leftovers that became new lanes. The rules that would have stopped it already existed among 434 IDs and were not followed. Evidence: `eval/audit-2026-10-14-session-slowness/FINDINGS.md`, `run-013-frictions.md` there, and `proposals/audit-rules-cost-2026-10-14.md`.

Home: the always-loaded text is `global/CLAUDE.md`; the template `CLAUDE.md` and `AGENTS.md` repeat only what a repository needs. A new rule enters here only with a measured defect it prevents (MAINTAINING M14).

## Scope and slicing

| ID | Rule | Why | Replaces |
|---|---|---|---|
| CR01 | Before the first dispatch or the first edit of a delivery, state the goal, what is out of scope and an estimate in minutes, and get the user's yes | Run 013 switched from docs to "implement everything" with no estimate | SA60, SA62, CE17 |
| CR02 | A delivery is one vertical slice (one area or one engine, about 30 changed files or 2 hours, its own PR); bigger work is cut into slices before any code; a widened scope is answered with the estimate and the slices first | Run 013 touched 269 files in one delivery | SA34, SA35, SA63 |
| CR03 | Defects first, structure later: each defect an audit or review finds ships first as the smallest fix in the current structure, with its test and PR; a restructuring is a separate delivery | The six defects of triage 3544 waited behind a two-engine restructure that never reached a PR | new |
| CR04 | Size L writes one short plan (about 100 lines: decisions, slices, acceptance items); S and M write no plan files | A 288-line design, a 520-line rule sheet and a 203-line plan were reread by every executor | WF26, WF27, DS49, SA64 |
| CR05 | Size L gets a design review before the plan: boundary fields from both sides, safety nets, personal data in new storage, logs or prompts, the rollout path | Three of the seven High findings of run 013 were design gaps found after the code | new; folds SA65 earlier |
| CR06 | One code path: a flag decides at the edge; old and new paths inside modules need a written rollback reason | "Sessions in flight keep the old rules" doubled every module of run 013 | SA24 |

## Executing

| ID | Rule | Why | Replaces |
|---|---|---|---|
| CR07 | The session that executes a slice writes the code itself; subagents only for the final review, a truly independent slice (own worktree, at most 2 executors), or heavy reading kept out of the main context | Each cold agent rereads the same documents; the only clean parts of run 013 were single-owner ones | SA13, SA36, SA53, SA63 |
| CR08 | A subagent prompt carries the goal, the acceptance items and at most about 5 paths; it returns at most 15 lines (done, files, tests, gaps, minutes) and never opens a subagent | Bounded input and output | SA04, SA06, SA12, SA22, SA37, SA45 |
| CR09 | `model` on every dispatch: sonnet by default, opus with a one-line reason | 47% of subagent turns ran on Opus by inheritance (FINDINGS F11) | SA14, SA33 |
| CR10 | Cadence: a running total of minutes against the estimate; report and stop at each slice end and at 1.5 times the estimate; no lane for leftovers without the user; an agent past about 150k tokens hands back | Agent returns carried 37 to 53 minutes each and nobody summed them | SA15, SA16, SA19, SA48 |
| CR11 | One phase per session for size L; checkpoint past about 120k tokens | Long orchestrator contexts are resent on every call | SA41, SA61 |
| CR12 | Long commands in the foreground with a timeout under 600 s in a subagent; background only from the main thread; no polling; never kill by image name | Orphans and polling were measured before (LS32) | SA54, SA57, TS34 |
| CR13 | In a shared tree no `stash`, `reset`, `checkout`, `restore`, `commit --amend`; commit messages through a file | Lost sibling work (SA53) | SA53, WF78 |

## Tests

| ID | Rule | Why | Replaces |
|---|---|---|---|
| CR14 | Failing test first; unit tests offline with fakes and a per-test timeout | A hanging test held run 013 for over 500 s | TS01, TS11, TS12 |
| CR15 | Before handing back, run the slice's tests and the tests that import the files it touched; the full suite once per delivery against a baseline | "Only your own new test" let cross-lane breakage surface hours later | TS02 to TS05, TS43, global "Tests" |
| CR16 | Never loosen a safety assertion or regenerate a snapshot to get green; an unrelated failure is reported | Agents edited tests to get green (FINDINGS F09) | TS05, TS09, TS39 |
| CR17 | Output to a file, failures and summary only; `rtk proxy` for runners, linters and any parsed output | `rtk` rewrote git and grep output inside command substitutions | SA25, CE notes |

## Docs and review

| ID | Rule | Why | Replaces |
|---|---|---|---|
| CR18 | A rule change is shown as today versus proposed and confirmed first; the implementing commit updates the PRD row and its body says what was decided; git is the history | One record, no copies | WF10, WF15, DS12 |
| CR19 | TRD and area maps name files and entry points and are updated once per delivery, in its last slice | 104 TRD edits in one run of 013 | AR07, DS21 |
| CR20 | One review per delivery over the combined diff: acceptance items one by one, boundary fields from both sides, PRD rows and TRD names; risk reviewers in the same message | Per-wave reviews missed cross-repo defects (LS34) | SA40, SA64, SA65 |
| CR21 | Critical and High fixed and rechecked on the fix diff; Medium and Low ride along; at most 5 rounds; a worse round or an open Critical at round 5 stops | Bounded review | RV01 to RV07, WF82 |
| CR22 | Safety nets change only with the user's explicit yes, never inside a task, a fix or a test edit | Run 013 put unit context into the alarm classifier for every session without a flag | WF12, WF13, RV06 |

## Pending (next PRs)

The per-commit gates that these rules make unnecessary are removed in the following PRs, not here: exact-count and uniqueness checks of the ratchet, per-edge import allowlists, module ID headers, commit trailers, the docs-gate bookkeeping codes, and the prd-flow card and sheet format checks (`proposals/audit-rules-cost-2026-10-14.md` section 5). Until then they still run.

Removed by slice K4a (scripts and templates): the ratchet checks `duplicate_names`, `crowded_dirs`, `no_prd_id`, `long_feature_maps`, `invariant_gaps` and every count in the allowlist (file lists now, a stale entry warns); `commit_trailers.py`, `gates.sh trailers` and the CI trailers job; the targets `red`, `watch`, `prd-sweep`, `settings-check` and `context`, and `trailers` and `retro` inside `close`; the guard hook's redirect, `tee` and `cat >` denial outside the source and docs folders; the template duties for ID headers, per-commit maps, trailers and promote. Still pending: the prd-flow skill and agent rows.

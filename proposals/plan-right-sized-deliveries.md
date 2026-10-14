# Plan: right-sized deliveries (2026-10-14)

Status: superseded on 2026-10-14 by `proposals/audit-rules-cost-2026-10-14.md` (the owner asked for clear rules instead of new scripts). Kept for its evidence table; only O1, O3, O4, O7, O9 and the E3 fix of O8 survive, as rules CR02, CR07, CR05, CR06, CR17 of `rules/core.md` and a bug fix in the next release.

## Evidence

| ID | Source | Fact |
|---|---|---|
| E1 | clara-ai change 013, session of 2026-10-14, telemetry `.ai-kit/runs/feat-single-conversation-state/events.jsonl` | Docs done 12:35; execution 12:41 to 15:44 with 43 commits and no green full suite, no PR. 19 subagents, 2,724 tool calls: about 40% reading and searching, 22% source edits, 11% test edits, about 20% docs edits. 269 files touched, 973 edits; the core service edited 30 times by 4 agents, `test_architecture.py` 25 times by 5 agents. Every executor lane hit its budget and left leftovers that became new lanes (T6 went through 5 agents). The final review found 7 High, 3 of them design gaps (cross-repo frame with no reply, unit context reaching the alarm classifier unflagged, unmasked PII in a new table) |
| E2 | `eval/audit-2026-10-14-session-slowness/FINDINGS.md` | Implementation is 14% of subagent time (F02), 24% of writes hit product code (F03), rules exist but are detected after the fact (F10), the docs gate fails a third of the time on bookkeeping (D02), one rule change fans out to about 11 synced copies (D03) |
| E3 | `kit/scripts/verify.py::default_ref` | Globs `*-{slug}/plan.md`; a slug that already carries the number (`013-...`) never matches, so the ref falls to the merge-base of the first base in `BASES`: the wave-1 verify of E1 compared 1,739 files and failed with WinError 206 |
| E4 | E1 transcript | Rules SA19 (brake), SA24 (one path), SA53 (worktree), SA62 (scope fixed) and SA63 (area-sized) were in the global block and were not applied: the run was outside prd-flow, with `general-purpose` agents, and nothing mechanical stopped it |

## Diagnosis

The delivery was too coarse (two engines, 27 rules, 269 files in one delivery) and the process too fine (one named test per rule, one commit per finding, docs, maps and structure gates per task). Each small step paid the cost of re-understanding a huge change. The rules that would have stopped it are text only, so they do not act outside prd-flow.

## Changes

| ID | Change | Where | Measured by |
|---|---|---|---|
| O1 | **Slice cap.** A delivery is one vertical slice: one area or one engine, at most about 30 changed files and about 2 hours of execution, its own PR. A size L change is split into slices in the plan, each shippable behind its flag. When the user widens the scope mid-session, the orchestrator answers with an estimate and the smallest slice before any dispatch | global block "Orchestrating a delivery"; new SA67 in `rules/02-subagents.md`; prd-flow `reference/write.md` "Plan" (slice table); amend SA62, SA63 | files per delivery, wall-clock per delivery in retro |
| O2 | **No leftover lanes; budget brake.** A lane that ends with work left goes back to the user with what is left and the cost; the orchestrator never opens a lane for leftovers on its own. The plan carries an execution estimate; at 1.5 times the estimate the run stops and reports. `gates.sh watch --budget-min N` exits when the wall clock passes N, waking the chief | global block; amend SA19; `kit/scripts/watch.py`; prd-flow `reference/dispatch.md` | new retro metrics `leftover_lanes`, `over_budget` |
| O3 | **One warm executor per slice; parallel only across slices, each in its own worktree.** Tasks inside a slice are sequential in one executor (cards become its checklist); two slices run in parallel only in separate worktrees. Executor ceiling for a slice: about 120 calls, replaced past about 150k tokens with a 10-line handoff | global block "Working with subagents"; amend SA13, SA15, SA53, SA63; `reference/dispatch.md` DP02, DP12 | `files_edited_by_3plus_agents` = 0, read share |
| O4 | **Design review before the plan (size L).** One reviewer pass over `design.md` (at most about 30 calls) checks every frame or field crossing a repository boundary from both sides, clinical and security safety nets, PII in any new storage or prompt, and the rollout paths; findings change the design, never the code | global block; new SA68; prd-flow `reference/run.md` "Review"; `prd-flow-reviewer.md` mode `design` | High findings at the final review that a design review would have caught |
| O5 | **Grounded plan, tests per finding.** Every card path in `Owns` exists or is marked `(new)`, checked by `gate.py --step plan` (`gate_waves.py`); the source list is mapped by finding or acceptance criterion to an acceptance test, rule IDs go to the trailer and module headers only (amend SA64) | `kit/.claude/skills/prd-flow/scripts/gate_waves.py`; `reference/write.md` "Card"; global block | plan gate errors on missing paths; tests per delivery |
| O6 | **Bookkeeping once per slice.** TRD body, area `CLAUDE.md` map, structure gates (ratchet, architecture test, allowlists) and the docs gate run once at the end of a slice by its executor; one owner edits allowlists | kit `CLAUDE.md` "Traceability"; `rules/05-code-structure.md` (AR07 wording "same slice"); amend WF80; `kit/AGENTS.md` | docs-gate runs per delivery, allowlist edits per delivery |
| O7 | **One code path.** The flag decides at the edge (session creation or the engine entry); "sessions in flight keep the old rules" is not offered as a default; a design that keeps old and new paths in every module needs a written rollback reason | amend SA24; `docs/templates` design question; prd-flow surveyor blind-spot line | design review finding count |
| O8 | **Verification that catches hangs and uses the right base.** Fix `verify.py::default_ref` (match `{slug}/plan.md` and `*-{slug}/plan.md`, prefer the configured base branch from `ai-kit.json`); per-test timeout in the stack recipes (pytest `--timeout`, vitest `testTimeout`) wired through `gates.sh one` and `verify`; `verify` includes the tests that import a touched module under every test root | `kit/scripts/verify.py`, `related_tests.py`; `stacks/*` recipes; `rules/04-testing.md` new TS27 | verify files compared, hangs surfaced per wave |
| O9 | **Raw output when it is parsed.** A command whose output feeds another command (`$(...)`, a pipe into a file list) runs through `rtk proxy` | global block "Tests"; `rules/01-context-economy.md` | none (instruction) |
| O10 | **Retro measures the waste.** `retro.py` reports read share, files edited by 3 or more agents, leftover lanes, wall clock against the plan estimate, and agents over 150k tokens | `kit/scripts/retro.py`, `retro_detectors.py`; `eval/METRICS.md`; `rules/11-telemetry.md` new TM18 | the metrics themselves (M07) |
| O11 | **Lesson.** LS35 records E1 and points to O1 to O10 | `rules/09-lessons.md`; `CHANGELOG.md` entry | none |

## Out of scope

- clara-ai test speed (E2 F08: TestClient waits, real sleeps, coverage on by default, no xdist): a project change, proposed to clara-ai after this rollout.
- Making the guard hook block an Agent call without `model` (E2 F11): candidate, needs a measurement first (M01).
- Finishing clara-ai change 013: its own sessions, under these rules.

## Execution

| Slice | Owns | Executor | Estimate |
|---|---|---|---|
| K1 rules and text: O1 to O7, O9, O11 | `global/CLAUDE.md`, `rules/01,02,04,05,07,09`, `kit/CLAUDE.md`, `kit/AGENTS.md`, prd-flow `SKILL.md` and `reference/{dispatch,run,write}.md`, `kit/.claude/agents/prd-flow-reviewer.md`, `CHANGELOG.md`, the runtime consistency tests they touch | one, worktree A | 45 to 60 min |
| K2 scripts: O2 watch budget, O5 plan grounding, O8 verify and timeouts, O10 retro | `kit/scripts/{watch,verify,related_tests,retro,retro_detectors}.py`, `gate_waves.py`, `stacks/*` timeout lines, `eval/METRICS.md`, `rules/11-telemetry.md`, their tests | one, worktree B | 60 to 75 min |
| Review | combined diff, item by item against this table | one reviewer | 15 min |
| PR | push the branch, PR to `main` | chief | 5 min |
| Rollout | `/ai-kit update` in clara-ai, agora-consulta-fe, modulo-integrador, each on a branch from its base, one PR each | one executor per repository, separate worktrees, in parallel | 30 to 40 min |

Total about 2.5 hours of wall clock. Budget brake (O2): stop and report at 4 hours. Cut if needed: O10 and the timeout part of O8 move to a second PR.

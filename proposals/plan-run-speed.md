# Plan: run speed (lessons of the assessment run, 2026-10-08/09)

Status: proposal, waiting for approval. Source run: clara-ai PRD 3 single assessment agent, then the backend and front contracts (PRs clara-ai#148, be-agoraconsulta#475, fe-agoraconsulta#236). Evidence: `run-timing-report.md`, deep dives A to F and `kit-improvements-consolidated.md` (scratchpad of session d012bb2c). Finding IDs (T, S, D, E, O) refer to that file.

## Why
| Item | Value |
|---|---|
| Wall time, clara-ai only | 432 min (16:11 to 23:25), backend and front the next day |
| Split | docs and survey 41%, code, review and close 36%, user wait 19%, chief 9% |
| Agent minutes | docs 169, surveyors 80, executors 258, reviewers 20 |
| Realistic saving | 120 to 150 min of the 432 without double counting (about 30%), and 28 to 38 of the 61 min of user wait |
| Biggest single wastes | baseline run 5 times, 3 of them inside docs agents (about 55 agent-min, 20 to 30 critical); a wrong domain model carried by the chief's prompts (about 37 min of user wait, about 65 agent-min of redo) |

## Goals and how they are measured
| ID | Goal | Metric (eval/METRICS.md or new) | Target on the next real run of size L |
|---|---|---|---|
| G1 | No baseline or full suite inside a docs agent; one baseline per plan commit | new `baseline_runs`, `runner_wall_min` | baseline_runs = 1 |
| G2 | No polling and no process alive at handback | new `poll_calls`, `bg_alive_at_return` | 0 and 0 |
| G3 | Fewer cold starts | `cold_starts`, `min_to_docs` | cold starts down 40% |
| G4 | Fewer user rounds lost to a wrong model | new `question_rounds`, `rejected_answers` | rejected answers at most 1 per change |
| G5 | Fewer fix dispatches | `review_rounds`, `rework_actions`, `first_pass` | fix dispatches down 40% |
| G6 | Telemetry per repository | events carry `repo`; retro of each repo non-empty | 100% |
| G7 | Wall time | `wall_min` on S5 and S8 not worse (adoption rule); next real run size L | 30% shorter |

## Workstreams

### W1. Tests and baseline (T1 to T9, E2, E6): about 60 to 90 agent-min, 25 to 35 critical
| Item | Change | Files | Rule | Test |
|---|---|---|---|---|
| W1.1 (T1) | `gates.sh baseline <slug> --bg`: runs in a git worktree at the plan commit, cached by commit plus lockfile hash, lock file, no-progress watchdog, deselect list from `tests.baseline_deselect`. Started by the chief right after the plan commit. Docs Plan step 4 and E03 "baseline before any executor" are removed; close checks the baseline exists | `kit/scripts/gates.sh`, new `kit/scripts/baseline.py`, `kit/ai-kit.json` (`tests.baseline_deselect`), `agents/prd-flow-docs.md`, `reference/execution.md` E03, `close_gate.py` | TS43 (amends TS04) | unit: cache hit, lock, worktree removed, deselect applied |
| W1.2 (T2, T7) | Related finder matches the full dotted path, ignores `__init__` and package-colliding stems, caps the selection (falls back to the owning folder with a note), passes files through an args file with `shell=False`; `gates.sh` uses `"$@"` | `kit/scripts/related_tests.py`, `gates.sh` | TS44 (amends TS07), TS49 | unit: `stages.py` vs `features.stages` imports, `__init__`, 200 files, paths with `(` and `[` |
| W1.3 (T4) | File walks use `git ls-files -co --exclude-standard`, no `resolve()` per file | `kit/scripts/kit_config.py`, `ratchet.py` | TS46 | timing test on a tree with a fake `node_modules` |
| W1.4 (T8) | `tests.always` (structure tests) always join `related`; close reruns only failing node ids of the last full run; the chief starts the full suite in the background during the last review | `related_tests.py`, `close_gate.py`, `kit/ai-kit.json`, `reference/execution.md` | TS50 (amends TS03) | unit: `always` added; close reuses a fresh run |
| W1.5 (T5) | Skip a rerun whose selection and content hashes are unchanged; `junit_xml` default per stack; drop `-p no:cacheprovider` from the recipes | `related_tests.py`, `stacks/python.md`, `stacks/node.md` | TS47 | unit: second identical call returns the cached summary |
| W1.6 (T6) | `gates.sh` resolves the interpreter once (`PY`), rejects the Windows Store stub, never calls bare `python`; agents never run `python -` heredocs or a bare `python` | `gates.sh`, executor, docs and surveyor "Common rules" | TS48 | unit: stub path rejected |
| W1.7 (T3, E2) | Long command rule in every agent file: explicit `timeout` up to 600000, foreground, no `until`/`sleep` loops, never return with a live process; mirror test while editing, one related run at the end, no chained edit plus test | executor, docs, surveyor, reviewer agent files; `global/CLAUDE.md` | TS45, TS51 | retro detectors (W5.3) |
| W1.8 (E6) | Delivery file line `Red: <first failing exit code>`; `gates.sh red <test>` runs one test expecting failure | executor agent, `gates.sh` | TS52 | unit |
| W1.9 (T9) | Install and update verify `tests.failure_regex` on a real failure line of the stack | `installer/ai-kit/reference/install.md`, `update.md` (K05) | IN17 | installer test |

### W2. Domain model, survey and questions (S1 to S7): 28 to 38 min of user wait, 55 to 65 critical
| Item | Change | Files | Rule | Test |
|---|---|---|---|---|
| W2.1 (S1) | Chief dispatch prompts carry no domain assumption; "user-confirmed" quotes the user's words and their scope; a prompt to another repo names only the request and the approved rows | `SKILL.md` Chief card, new `reference/dispatch.md` | WF65 | eval premise-trap scenario (W6) |
| W2.2 (S2) | Surveyor builds the domain model from the glossary, section intros and the journey before rows by ID; code facts are evidence, never question premises | `agents/prd-flow-surveyor.md`, `reference/impact.md` | WF66 | S5 to S7 `prd_fidelity` |
| W2.3 (S3) | Round 0: the model in one plain sentence for the user to confirm before any rule question; after two model corrections the chief stops and reconfirms the model | `SKILL.md` C5 route, `reference/interview.md` | WF67 | new `rejected_answers` |
| W2.4 (S4) | Question lint in `gate_interview.py`: each option cites the row it changes, one decision per option, a jargon list from repo.md, a "the scenario is wrong" option, never ask what a row already states | `reference/impact.md`, `reference/interview.md`, `gate_interview.py` | WF68 (amends WF15) | unit on the lint; judge grade |
| W2.5 (S5, S6) | Alignment gate inside prd-plan: an open TRD-only decision blocks the plan and joins the interview; each card's Contract covers the TRD IDs of its Owns; each created symbol has a non-test caller owned by a card | `gate_plan.py check_plan`, `agents/prd-flow-docs.md`, `reference/trd-planned.md` | WF69, WF70 | unit on `check_plan`; S2, L2, L3 `plan_drift` |
| W2.6 (S7) | Delta re-survey after a correction: only the touched rows and contexts, by the same surveyor resumed | `agents/prd-flow-surveyor.md`, `SKILL.md` | WF71 | `cold_starts` |

### W3. Docs agents and state (D1 to D8): 40 to 60 min
| Item | Change | Files | Rule | Test |
|---|---|---|---|---|
| W3.1 (D1) | Resume a warm agent with SendMessage when its context is valid and under about 150k tokens (approved by the user on 2026-10-09); a folded correction is an in-place `adjust`, not revert and redo | `SKILL.md` Chief card (drop "never message or resume"), `reference/execution.md` E07, `agents/prd-flow-docs.md` trd-plan adjust | SA48 (replaces SA31) | `cold_starts`, `min_to_docs` |
| W3.2 (D2) | One state record: `rules.md` (rows replaced in place, Rounds table, Dimensions, Confirmed lines) and `delta.md` (ID, op, files, one line); `interview.md`, `approved-rules.md` and `decisions.md` rendered from it; `state.md` split into `chief.md`, `survey.md`, `plan.md` | `reference/interview.md`, E08, `gate_interview.py`, `gate.py --rules`, `promote.py` readers | CE29 | unit on render and gates; `rereads`, `context_peak` |
| W3.3 (D3) | Fan-out routing writes a cross-context facts table (key names, invariants, owners, call sites); the merge concatenates, checks and gates | `agents/prd-flow-docs.md` context and merge | SA49 | L1 `contradiction_left` |
| W3.4 (D4) | Merge 3524bd2 (docs-html skill) to main before this plan; projects move to `html_mode: generated` after a preview | `installer/ai-kit/reference/update.md` | LS31 | S5 `min_to_docs` |
| W3.5 (D5) | `promote.py` reads markers from repo.md (`planned_source`, the approved marker), `--hold ID` for partial promote, fails on a delivered rule without Source (also frontend and backend routes), realigns the state record after promote | `promote.py` l.130 and l.247, `gate_core.py` NON_CODE_ROUTES, executor close step | WF72 (amends WF61) | `tests/test_promote.py`: pt-BR markers, hold, missing Source |
| W3.6 (D6) | `gate.py --docs <slug>`: rules, prd, trd, plan and applied in one process with an mtime cache; `gates.sh docs` calls it | `gate.py main`, `gates.sh docs` | DS46 | unit: second call reuses the cache |
| W3.7 (D7) | Dispatch ledger in the chief record; docs and executor agents have an "already applied" fast path | `SKILL.md` State, docs and executor agents | SA50 | `rework_actions` |
| W3.8 (D8) | `gate.py --final --change <slug>`: scoped by the change's rows, its Planned heading and its folder; a snapshot of older drift at classification | `gate_plan.py check_final`, `close_gate.py`, `gate.py` | WF73 (amends WF33) | fixture with seeded old drift |

### W4. Plan and executors (E1 to E5, E7): 30 to 45 agent-min
| Item | Change | Files | Rule | Test |
|---|---|---|---|---|
| W4.1 (E1) | Card field `Reached from:` (entry point or caller); a wiring task per feature at the end of each plan; plan gate fails on Owns over 8 files or no test path | `reference/agent-plan.md`, `gate_plan.py check_plan`, `gate_waves.py` | WF74 | S8 expected tasks; L2 and L3 |
| W4.2 (E4) | Executor self-check in the delivery file, read first by the reviewer: call sites wired, structure tests, size caps, key-off parity, PII in logs and prompts, soft-delete and tenant scope in queries, guard plus counter-example test | executor and reviewer agents, delivery format | SA52 | `first_pass`, `review_rounds` |
| W4.3 (E3) | Code edits only with Edit and Write; scripts only move code; a PreToolUse hook warns on `sed -i`, `python -` and heredoc writes to source files | executor agent, `kit/.claude/settings.json`, new hook script | SA51 | hook unit test |
| W4.4 (E5) | PreToolUse hook blocks `git stash`, `reset`, `checkout`, `restore`, `commit --amend` and repo-wide `gates.sh fix` for prd-flow agents; one owner per shared file per wave (ai-kit.json, structure allowlists, settings module); a worktree per executor in waves of 3 or more | `reference/execution.md` E22 and E05, settings hook, `gate_waves.py` | SA53 | hook unit test; S8 wave 1 |
| W4.5 (E7) | Review per wave stays; Medium and Low of a round go to one batched fix; a Medium round counts toward the review cap | `reference/review.md` V01, V02, V04, `SKILL.md` Review line | RV18 (amends RV01) | `review_rounds`, `rework_actions` |

### W5. Orchestration and telemetry (O1 to O4): 25 to 40 min
| Item | Change | Files | Rule | Test |
|---|---|---|---|---|
| W5.1 (O1) | Background and parallel by default for every dispatch; a whole wave in one message; the surveyor verifies and prepares questions in one step | `SKILL.md` Chief card and C5 step 6, E04 | SA54 | `parallel_factor`, `runner_wall_min` |
| W5.2 (O2) | Cross-repo mode: `.ai-kit/repos.json` (alias, path, adapter, interpreter), `Repo: <alias>` in prompts; per-repo state; parallel-safety and unit-only rules live in the agent files, not the prompts | new `reference/dispatch.md`, `SKILL.md`, agent files | SA55 | new cross-repo scenario |
| W5.3 (O3, T3, T9) | Telemetry: per-event `repo` derived from the command and file paths; agent mode, task, slug, model and bg; Bash bg, timeout and auto_bg; AskUserQuestion `wait_ms`; `wait.test` class; SubagentStop `dur_ms`; chain classification; retro detectors for polling and live background processes; chief generation time in the retro | `telemetry_hook.py`, `retro.py`, `retro_detectors.py` | TM14, TM15, TM16 | `tests/test_kit_telemetry_hook.py`, `tests/test_kit_retro.py` |
| W5.4 (O4) | Install checks `rg` on PATH and documents `rtk proxy` for test runners | `installer/ai-kit/reference/install.md`, `global/CLAUDE.md` | IN18 | installer doc |

### W6. Evaluation (MAINTAINING M01, M07)
| Item | Change |
|---|---|
| W6.1 | New metrics in `eval/run.py` and `METRICS.md`: `baseline_runs`, `poll_calls`, `bg_alive_at_return`, `question_rounds`, `rejected_answers`, `bash_code_edits`, `git_unsafe_calls` |
| W6.2 | New scenarios: S9 premise trap (a dispatch prompt carries a wrong domain model the PRD contradicts), S10 slow suite (a fixture whose suite takes about 2 min, to show baseline and polling waste), S11 cross-repo contract |
| W6.3 | Predictions in `eval/predictions/run-speed.md`, then one round of `arms-big.json` (S5 at 2 reps, S8) base vs candidate, audited by `efficiency-auditor`; adoption by the existing rule |
| W6.4 | Lesson LS31 in `rules/09-lessons.md` with this run's numbers |

## Execution
Branch `feat/run-speed` from main after 3524bd2 is merged. Waves with disjoint ownership, executors on sonnet, review per wave:

| Wave | Tasks (parallel) | Owns |
|---|---|---|
| 1 | K1 scripts: W1.1 to W1.6, W1.8, W3.6, W3.8 | `gates.sh`, `baseline.py`, `related_tests.py`, `kit_config.py`, `ratchet.py`, `close_gate.py`, `gate.py`, `gate_plan.py check_final` |
| 1 | K2 promote and state: W3.2, W3.5 | `promote.py`, `gate_core.py`, `gate_interview.py`, state renderers |
| 1 | K3 telemetry: W5.3 | `telemetry_hook.py`, `retro*.py` |
| 1 | K4 hooks: W4.3, W4.4 hook scripts | new hook scripts, `kit/.claude/settings.json` |
| 2 | K5 skill and references: W2.1, W2.3, W2.6, W3.1, W3.7, W4.5, W5.1, W5.2 | `SKILL.md`, `reference/*.md` |
| 2 | K6 agents: W1.7, W2.2, W2.4 text, W3.3, W4.2, W4.1 text | `kit/.claude/agents/prd-flow-*.md`, `reference/agent-plan.md` |
| 2 | K7 plan gate: W2.4 lint, W2.5, W4.1 gate | `gate_plan.py check_plan`, `gate_waves.py`, `gate_interview.py` lint |
| 3 | K8 rules, installer and docs: rule rows, W1.9, W5.4, CHANGELOG with `On update:` lines, README, MAINTAINING | `rules/`, `installer/`, `CHANGELOG.md` |
| 3 | K9 eval: W6.1, W6.2, predictions | `eval/` |
| 4 | Round: W6.3 (cost about US$18 to 25), verdict, LS31 | `eval/results/` |

Every script change has a unit test (`python -m unittest discover -s tests`). The skill size and structure tests stay green.

## Replication to the three repositories
| Step | Action |
|---|---|
| R1 | Merge `feat/run-speed` to main and push; `git pull` in `~/.ai-starter-kit` (it is on 3e66f2f, behind); `./install.sh` |
| R2 | In each repo, a branch `chore/ai-kit-update` from staging, `/ai-kit update` (all 59 to 70 kit-owned files match their manifest, so replacement is clean) |
| R3 | Project-owned edits through `On update:` lines or by hand: `tests.baseline_deselect` (clara: the hanging offline-gate test), `tests.always`, `junit_xml`, the backend `failure_regex` (`^FAIL\s+(\S+)`), the PreToolUse hooks in `.claude/settings.json`, `html_mode: generated` after a preview |
| R4 | `scripts/gates.sh setup`, ratchet, docs and the unit suite per repo; one PR per repo |
| R5 | Next real delivery runs on the new kit; its retro is compared with this run (goals G1 to G7) |

## Decisions for the user
| ID | Decision | Recommendation |
|---|---|---|
| Q1 | Scope | All six workstreams in four waves, as above |
| Q2 | Base | Merge 3524bd2 (docs-html) to main first, then branch |
| Q3 | Proof | This run is the real-project evidence (M01); one eval round (W6.3) before replication |
| Q4 | Hooks | Block unsafe git only for prd-flow agents; warn (not block) on script edits |
| Q5 | Replication | One `chore/ai-kit-update` PR per repo, after the three feature PRs are merged or in parallel |

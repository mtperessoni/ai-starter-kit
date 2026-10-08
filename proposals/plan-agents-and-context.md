# Plan: subagent and context management for prd-flow

Status: validated by the maintainer on 2026-10-08 (decisions D1 to D4 below); execution pending R0. Sources: `proposals/efficiency-audit.md` (my audit), `eval/AUDIT-prd-flow.md` (second audit, findings A1 to A12, B1 to B9, C1 to C3, EV1 to EV4), four eval rounds. Scorecard: `eval/METRICS.md`.

## Diagnosis in one paragraph
Cost and time follow the number of main-thread calls on the strongest model at 80k to 130k context. The main makes 50 to 55 calls per change (prd-gate: 25 to 38), and 53% to 66% of them come after the executor (Promote with no owner, diff reads, gate debugging, closing ceremony). Agents are not too expensive by themselves (a Sonnet agent costs about a quarter of the same work done in the main); they are spawned without a clear owner, a bounded input or a bounded output, so work leaks back into the main, steps get skipped or done twice, and every agent explores instead of reading a pack. Instructions grew with each fix and became contradictory, which is where the S5 contradiction and the skipped steps come from.

## Principles
| ID | Principle | Replaces |
|---|---|---|
| AG1 | **Spawn with a reason.** An agent exists only when it needs another model, keeps more than a few reads out of the main, or runs in parallel. Each role has one owner and appears once in the dispatch map | "Always dispatched" rules argued away by the model |
| AG2 | **The main is a thin conductor.** Allowed: `repo.md`, one INDEX Grep, the surveyor's confrontation, worker returns, state files it owns, `git commit` with a file list, one `gate --rules`, one close call. Forbidden: PRD, TRD or source reads before the surveyor; edits under `docs/` or the source folders; reading diffs' content; debugging the gate; reading worker-only references. Every violation is a metric (`main_violations`) | Scattered "does not" sentences |
| AG3 | **Bounded input.** Every dispatch names its pack: the briefing file, the state files and the exact PRD, TRD and source paths or symbols it may read. The surveyor builds the pack once; the planner writes a read list per task; nobody explores beyond it | Workers rereading the repository from scratch |
| AG4 | **Bounded output.** Results land in state files; the return is at most 10 to 20 lines; the main never reopens worker files | Long returns pulled into the main context |
| AG5 | **Bounded loops.** At most 2 reruns per step; the third failure returns the ERROR lines as a gap | Unbounded "fix and run again" (47 gate runs in r2) |
| AG6 | **No fragile tricks.** No SendMessage resume that needs a ToolSearch (it rewrote 69k to 85k cached tokens and never worked); a new agent with the pack instead | `5409e23` resume rule |
| AG7 | **Scripts only for deterministic multi-step chores** that today cost several main calls: Promote mechanics and the closing checks. Two scripts, not a scripting layer | Promote and closing done by hand in the main |
| AG8 | **Models by role.** Judgment (surveyor, planner) on the strongest model at high reasoning effort; typing (writers, executors, reviewer) on the fast model; the main stays the user's session but thin | Opus spent on edits, Sonnet on conflict judgment |

## Orchestration techniques (review of 2026-10-08)
The cost model behind every rule below: a token that enters the main context is paid again on every later main call (context residency). 20k tokens read inline at call 10 of 50 are resent 40 times, about 800k tokens on the strongest model; the same reading in an agent costs its cold start (about 23k) times its own calls, on the fast model, and only its 10 to 20 return lines enter the main.

| ID | Technique | How | Why it saves |
|---|---|---|---|
| AG9 | **Spawn rule by residency.** Inline only what the main must hold anyway (the user's answers, a return, one short command). Anything that reads more than about 8k tokens or 3 files whose content the main does not need goes to an agent | A table in the main card: inline versus agent, by action | Stops both leaks seen in the data: the main reading PRD/TRD/code "to have context", and agents spawned for one-line chores |
| AG10 | **Granularity by the critical path.** A task is at least one file and its test. Tasks are split only when the pieces can run in parallel on the critical path; sequential pieces of one area are one task. A one-rule change is one executor task | Planner rule plus `gate.py --step plan` warning on serial tasks of the same area | Today a 1-task change still spawns 5 to 6 agents; a feature keeps its parallel width |
| AG11 | **Waves computed, not reasoned.** `gate.py --step plan` prints the wave table from `Depends on` and `Owns` (topological order, critical path first, at most 4 executors per wave) and fails when two tasks of one wave share a file in Owns | Deterministic; the main dispatches each wave in one message, background, no polling | Parallelism for features without the main reasoning over the DAG; no colliding parallel executors |
| AG12 | **Task card in the prompt, the rest by path.** The executor prompt carries its task section (at most 25 lines: contract, Owns, read list, tests, commit line); the briefing, rules and deliveries blocks stay files it reads only if needed | Planner writes cards; main pastes the card | Saves 2 to 4 read calls per executor (each a turn), and keeps the card in the prompt cache |
| AG13 | **Shared prompt prefix for siblings.** Every agent of one role gets the same leading text (stable briefing path and plan header, no timestamps or run IDs first); the task-specific line comes last | Prompt template in the main card | Parallel executors of one wave hit the same cached prefix |
| AG14 | **Interfaces before parallel work.** Parallel tasks get their shared names from the plan's `Creates / consumes` (signatures, file names) and read the producer's `deliveries.md` block, never the producer's code | Planner rule, already partly there | Parallel executors do not wait or explore each other's code |
| AG15 | **One reviewer per wave, on the combined diff.** The reviewer reads the wave diff range and the rule IDs, not the repository; a second round only after a Critical or High fix, scoped to the fix diff | Review table (A5) | One review agent per wave instead of per task |
| AG16 | **Main context budget and checkpoint.** When the main passes about 120k tokens or a feature has more than 2 waves left, it writes `state.md` and continues in a fresh session with `/prd-flow resume <slug>`, which reads only `state.md` and the current wave | Rule E01 extended with a token threshold | Long features stop paying a growing context on every call |
| AG17 | **No mid-run tool loading.** Tools needed by the flow are known at start; the main never calls ToolSearch during a C5 | Main card | A deferred-tool load rewrote 69k to 85k cached tokens |
| AG18 | **Fast model for small mechanical agents.** Scoped re-review and checks that only confirm a fix may run on the cheapest model | Model column in the dispatch table | Pays strong-model prices only for judgment |

## Agent map by case
| Case | Agents, in order | Main does |
|---|---|---|
| C1 query | none | answers with IDs, one Grep per Source |
| C3 bug, C6 refactor | executor, reviewer | classify, confirm, commit, close |
| C4 stale PRD | writer-prd | confirm the divergence, commit |
| C5 size M (one area) | surveyor (strong) → docs (PRD, TRD and plan in one context) → executor(s), parallel when Owns are disjoint → reviewer (one round; a second only after a Critical or High fix) | confrontation, interview, approval, commits, `promote.py` + `gates.sh close` |
| C5 size L | surveyor (strong) → docs (PRD, TRD and plan; strong for the plan part) → executor waves from `--step plan` (at most 4 in parallel, disjoint Owns) → one reviewer per wave → last task merges the TRD | same, plus plan approval, dispatch per wave, checkpoint per AG16 |

Agents per change, target: one-rule change 3 to 4 (surveyor, docs, executor, reviewer); a feature with N independent tasks 3 + N executors in about ceil(N/4) waves + one reviewer per wave. Width comes from the plan's graph, never from the habit of one agent per step.

Promote: `promote.py <slug>` does the mechanics (drop markers, fill Source from the TRD Planned rows, CHANGELOG literal excerpts, fold, HTML rebuild, archive, `gate --final`); the TRD Planned merge, which needs judgment, is part of the last executor's task with `docs/trd/<area>.md` in its Owns, never a hidden step.

## Correctness first
| ID | Fix |
|---|---|
| A2 | New sweep K14: a rule stated without condition that the new rule makes false for some input is a conflict, resolved by rewriting the same row (same ID, same file; the old text goes to `## Supersedes` as `ID: old text`). Gate Q5: every ID named in the surveyor's `Conflicts:` has a resolution in `approved-rules.md` (rewritten row, superseded, or `compatible: <reason>`). Remove the r3 sentence that kept conflicting rows out of the table |
| B1, B2 | `--base` with a missing ref is an ERROR, never a false green; without `origin/<base>` fall back to the local base branch, else WARN |

## Instruction diet
| Change | Measure |
|---|---|
| A "main card" in SKILL.md (about 15 lines) with AG2, the step-4 formats and the step-10 loop; `execution.md`, `review.md` and E12 to E19 become worker-side | skill bytes read by the main per run |
| The why and the measured numbers live in `rules/` and the lessons, never in runtime files | SKILL.md at most 6 KB, ratchet on skill bytes |
| One home per rule; contradictions removed (A5 review policy, A6 size table, A7 deliveries path, A10 who runs `--rules`) | `main_violations`, `dispatch_map` |
| Script friction fixed where it costs turns: B3 G7 marker, B4 one base resolver, B5 HTML path, B6 untracked files, B7 lint prints a result, B8 every ERROR says the fix | `rework_actions`, `max_reruns_per_step` |

## Rounds (one change each, `eval/METRICS.md`)
| Round | Change | Must move | Cost |
|---|---|---|---|
| R0 | Hermetic eval (temp config dir, pinned model and effort), new metrics (`main_calls`, `main_tokens_post_exec`, `dispatch_map`, `main_violations`, `conflict_recall`, `rework_actions`, `max_reruns_per_step`, `first_pass`, `review_weighted`), base and current head at 3 reps on S5 | a trustworthy baseline | about US$35 |
| R1 | Correctness: A2, B1, B2 | `contradiction_left` 0, `conflict_recall` 1.0 | about US$25 |
| R2 | Agent map, main card with the spawn rule (AG9), Promote ownership plus `promote.py`, `gates.sh close`, AG5, AG6, AG17 | `main_calls` at most 30, `main_tokens_post_exec` at most 1.5M, `dispatch_map` 1.0, agents per one-rule change at most 4 | about US$25 |
| R2b | Parallel work: granularity (AG10), computed waves and the Owns overlap check (AG11), task cards (AG12), shared prefixes (AG13), one reviewer per wave (AG15), checkpoint (AG16). Measured on a new small-fixture scenario **S8**: a feature with three tasks, two of them independent | `parallel_factor` (agent minutes during execution over execution wall) at least 1.5 on S8, wall time of S8, no overlap collisions, S5 to S7 not worse | about US$30 |
| R3 | Context packs (AG3) and the instruction diet | reads per agent, skill bytes, `wall_min` | about US$25 |
| R4 | Remaining script friction (B3 to B9) | `rework_actions`, error rate | about US$25 |

Each round is adopted only on its own measured delta; a failed round is reverted or explained before the next.

## Decisions of the maintainer (2026-10-08)
| ID | Decision | Chosen |
|---|---|---|
| D1 | Step 6 (the user confirms the PRD diff before the TRD) | **Skipped when proven:** when `--applied` is green and there are no non-table changes, one docs agent writes PRD, TRD and plan; the approval stays the row-by-row one of step 4. A rule change of the flow: it goes through the kit's own PRD-first route (rules catalog, SKILL.md, CHANGELOG) in R2 |
| D2 | Strong model for the surveyor and the planner | **Every C5**, high reasoning effort where the platform allows it |
| D3 | Eval budget | **R0 to R2 first** (about US$85); R3 and R4 decided with their numbers |
| D4 | TRD Planned merge at the end | **The last executor task**, with `docs/trd/<area>.md` in its Owns; `promote.py` does the rest |

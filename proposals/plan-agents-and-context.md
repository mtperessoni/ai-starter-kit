# Plan: agents and context for prd-flow

Status: validated by the maintainer on 2026-10-08 (decisions D1 to D6); execution starts at R0, budget R0 to R2b. Sources: `proposals/efficiency-audit.md`, `eval/AUDIT-prd-flow.md` (findings A1 to A12, B1 to B9, C1 to C3, EV1 to EV4), four eval rounds. Scorecard and adoption rule: `eval/METRICS.md`.

## 1. Goal
The fewest tokens, the shortest wall time, the best output, the fewest errors, for every request the flow runs, from a one-rule change to a multi-wave feature. Nothing is adopted on belief: every item below names the metric it must move and is measured alone (section 9).

## 2. Diagnosis
Cost and time follow the number of main-thread calls on the strongest model at 80k to 130k context: 50 to 55 per change today (prd-gate: 25 to 38), 53% to 66% of them after the executor. Agents are not the expensive part (a Sonnet agent costs about a quarter of the same work in the main); they are spawned without an owner, a bounded input or a bounded output, so work leaks back to the main, steps are skipped or done twice, and every agent explores instead of reading a pack. A one-rule change spawns 5 to 6 agents for a 1-task plan. Instructions grew 44% with each fix and contradicted themselves; that is where the S5 contradiction and the skipped steps come from. Scripts are fast (gate 1.1 s, HTML 0.15 s) and the cache is healthy (0.94 to 0.97); neither is the problem.

## 3. The cost model behind every rule
| Fact | Consequence |
|---|---|
| A token in the main context is resent on every later main call (residency): 20k read at call 10 of 50 cost about 800k tokens on the strongest model | The main reads only what it must hold; everything else is read where it is used |
| An agent costs its cold start (about 23k tokens) times its own calls, on the fast model, and returns 10 to 20 lines | Spawn when the work would leave more than that in the main |
| Every tool call is a model turn that resends the context | Fewer, larger, deterministic steps; scripts for multi-step chores |
| The prompt cache matches prefixes and expires; a deferred-tool load or a long user pause rewrites it | Stable prefixes, no mid-run tool loading, interview while the main is still small |

## 4. Principles of agent management
| ID | Principle |
|---|---|
| AG1 | **Spawn with a reason:** another model is needed, the work keeps more than a few reads out of the main, or it runs in parallel. One owner per role, once in the dispatch map |
| AG2 | **Thin main with a contract.** Allowed: `repo.md`, one INDEX Grep, the surveyor's confrontation, worker returns, its state files, `git commit` with a file list, one `gate --rules`, one close call. Forbidden: PRD, TRD or source reads before the surveyor; edits under `docs/` or the source folders; reading diff content; debugging the gate; worker-only references. Every violation is counted (`main_violations`) |
| AG3 | **Bounded input:** every dispatch names its pack (briefing, state files, exact paths or symbols); nobody explores beyond it |
| AG4 | **Bounded output:** results go to state files; the return is 10 to 20 lines; the main never reopens worker files |
| AG5 | **Bounded loops:** at most 2 reruns per step; the third failure returns the ERROR lines as a gap |
| AG6 | **No fragile tricks:** no SendMessage resume that needs a ToolSearch; a new agent with the pack |
| AG7 | **Scripts only for deterministic multi-step chores:** `promote.py` and `gates.sh close` |
| AG8 | **Models by role:** surveyor and planner on the strongest model at high effort; writers, executors and reviewer on the fast model; mechanical confirmations on the cheapest (AG18) |
| AG9 | **Spawn rule by residency:** inline only what the main must hold (the user's answers, a return, a short command); more than about 8k tokens or 3 files the main does not need go to an agent |
| AG17 | **No mid-run tool loading:** the main never calls ToolSearch during a C5 |
| AG18 | **Cheapest model for mechanical checks:** a scoped re-review that only confirms a fix, the closing checks |
| AG19 | **Roles as defined subagents.** Each role is `.claude/agents/prd-flow-<role>.md`: its briefing is the system prompt (cached, no reads to start), its model is pinned, its tools are the minimum (surveyor and reviewer read only; executor without web tools). The main dispatches by `subagent_type`, with a prompt of the slug, the state folder and the task card only |

### Models by role
| Role | Model and effort | Tools | Why |
|---|---|---|---|
| Main (planning session) | the user's session, strongest model | all | confrontation and interview are judgment with the user |
| Main (execution session, D5 arm) | fast model | all | dispatch, commit, close |
| surveyor | strongest, high | Read, Grep, Glob, Bash (read only) | conflict judgment: the S5 miss came from here |
| docs (PRD, TRD and plan) | strongest, high | Read, Grep, Glob, Edit, Write, Bash | the plan decides waves and granularity |
| executor | fast | Read, Grep, Glob, Edit, Write, Bash | typing against a card |
| reviewer | fast | Read, Grep, Glob, Bash (read only) | findings on a diff |
| re-check (scoped) | cheapest | Read, Grep, Bash (read only) | confirms a fix |

## 5. Choosing what to parallelize
| ID | Technique | Rule |
|---|---|---|
| AG10 | **Granularity by the critical path** | A task is at least one file and its test; split only when the pieces run in parallel; sequential pieces of one area are one task; a one-rule change is one executor task |
| PX1 | **Split economics** | Split a task only when each piece is at least about 10 tool calls of work and independent; a smaller piece rides with its neighbor, because its cold start and rereads cost more than the minutes it saves |
| PX2 | **Context affinity** | Tasks that read the same large files (a big module, the same area map) go to the same executor; parallel agents each rereading one big file pay it N times |
| AG11 | **Waves computed, not reasoned** | `gate.py --step plan` prints the wave table from `Depends on` and `Owns`, critical path first, and fails when two tasks of one wave share a file |
| PX3 | **Width cap and dispatch** | At most 4 executors per wave, dispatched in one message in the background, no polling; a failed task reruns alone; on rate limits the wave shrinks to 2 |
| AG14 | **Interfaces before parallel work** | Shared names come from the plan's `Creates / consumes` and the producer's `deliveries.md` block, never from the producer's code |
| AG15 | **One reviewer per wave** | On the combined wave diff and the rule IDs; a second round only after a Critical or High fix, scoped to the fix diff |
| PX4 | **Pipelining, only when measured** | For size L with slices: the review of wave k may overlap wave k+1 when k+1 owns none of k's files; plan slice 2 while slice 1 executes. Adopted only if S8 shows a wall-time gain without rework |
| PX5 | **Isolation only when needed** | A worktree per executor only when parallel tasks share build or test state that interferes (LS09); otherwise one tree with disjoint Owns |

Target agents per change: one-rule change 3 to 4 (surveyor, docs, executor, reviewer); a feature with N independent tasks 3 + N executors in about ceil(N/4) waves, one reviewer per wave.

## 6. Context and artifacts
Artifacts make sense when they replace rereading, not when they add reading. Each one has one writer, a size budget, an ID-indexed layout readers can Grep then read by range, and a validity key.

| ID | Technique | Rule |
|---|---|---|
| CX1 | **Artifact contract** | Small, typed, single writer, budgeted (pack 120 lines, card 25 lines, deliveries block 8 lines, return 20 lines); pass paths, not content; paste only a card of at most 25 lines into a prompt, because a Read costs a turn |
| CX2 | **Two caches** | The TRD is the cross-change cache (where things live, verified by `gate --trd`); `pack.md` is the per-change cache (literal rule rows, file and symbol map, conflicts), valid while `git diff --quiet <base> -- <pack paths>` holds; docs, planner and executors read the pack excerpt they need, never the PRD or TRD again |
| AG12 | **Task card in the prompt** | The executor prompt carries its task section (contract, Owns, read list with symbols, tests, commit line); the rest by path |
| AG13 | **Shared prompt prefix** | Agents of one role share the leading text (stable paths, no timestamps); the task line comes last, so siblings hit the same cached prefix |
| CX3 | **Read budgets per role** | Surveyor about 40k, docs about 30k, executor about 25k tokens of reading; Grep first, then Read by range; big files by symbol only |
| CX4 | **Tool output hygiene** | Tests and lint to a file with one result line (B7); `git diff --stat` and `--name-only` in the main; gate output scoped and capped (done); never cat a whole file |
| CX5 | **Cache-aware order** | The interview runs at step 4 while the main is still small (a user pause past the cache lifetime rewrites the whole main context); questions batched, at most 4 per round |
| AG16 | **Main checkpoint** | Past about 120k tokens, or with more than 2 waves left, the main writes `state.md` and continues in a fresh session with `/prd-flow resume <slug>` |
| CX6 | **Execution session on the fast model** | After the plan is approved, execution can continue in a fresh session on the fast model: the main only dispatches, commits and closes there (decision D5) |
| CX7 | **Doc size budgets** | A PRD section file gets a line budget like the TRD (`prd_section_budget_lines`, warned by the gate), so packs stay bounded as the product grows |
| CX8 | **Artifact cleanup** | Promote keeps only what is durable (CHANGELOG, decisions); state packs and gate logs of a closed change are deleted |

## 6b. Many PRDs and TRDs, one per system context
The kit's model is one PRD per product context or feature that runs on its own (`prd-create` anatomy "How many PRDs"), each split into section files, and one TRD file per code area. Every rule of this plan must hold when a repository has many of them.

| ID | Rule |
|---|---|
| MP1 | **INDEX is the router.** `docs/prd/INDEX.md` has one section per PRD; the main greps it (never reads it whole) and the surveyor picks candidate sections across every PRD for K11 and K14, because a conflict can live in another context's PRD |
| MP2 | **Packs and approved rules span PRDs by file.** `pack.md` and `approved-rules.md` group rows under `## <prd folder>/<file>.md`; the gate checks each file; nothing assumes one PRD |
| MP3 | **Docs fan-out by context.** A change that touches two or more PRDs or TRD areas, each with more than about 5 rows, gets one docs agent per context in parallel (disjoint files), and one planner merge; otherwise one docs agent |
| MP4 | **Executor affinity by area.** Waves group tasks by TRD area (PX2); parallel width comes from independent areas |
| MP5 | **A new context is a new PRD.** A request for a new product context in a repository that has PRDs is C5 size L, new-PRD variant: the docs agent lays out the folder with the prd-create anatomy and adds its INDEX section and HTML tab |
| MP6 | **Budgets per context.** Section files, TRD files and packs have line budgets (CX7), so the cost of a change stays proportional to the contexts it touches, not to the size of the product |
| MP7 | **Shared contexts across repositories** stay checked by `--sibling` (G28) for the PRDs listed in "Shared PRDs" |

## 7. Agent map by case
| Case | Agents, in order | Main does |
|---|---|---|
| C1 query | none | answers with IDs, one Grep per Source |
| C3 bug, C6 refactor | executor, reviewer | classify, confirm, commit, close |
| C4 stale PRD | writer-prd | confirm the divergence, commit |
| C5 size M | surveyor (strong) → docs (PRD, TRD and plan; step 6 skipped when proven, D1) → executor → reviewer | confrontation, interview, approval, commits, `promote.py` + `gates.sh close` |
| C5 size L | surveyor (strong) → docs (strong for the plan) → executor waves from `--step plan` → one reviewer per wave → the last task merges the TRD (D4) | same, plus plan approval, waves, checkpoint (AG16), optional fast-model execution session (CX6) |

## 8. Correctness, diet and friction
| Area | Items |
|---|---|
| Correctness | A2 conflict sweep K14 (an unconditional rule the new rule makes false is rewritten in the same row) and gate Q5 (every conflict resolved); remove the r3 sentence that kept conflicting rows out of the table; B1 false green on a missing base; B2 base fallback |
| Instruction diet | A main card of about 15 lines in SKILL.md; `execution.md` and `review.md` worker-side; the why and measured numbers live in `rules/`, never in runtime files; SKILL.md at most 6 KB with a ratchet on skill bytes; contradictions removed (A5 review policy, A6 size table, A7 deliveries path, A10 who runs `--rules`) |
| Friction | B3 G7 on marker removal, B4 one base resolver, B5 HTML path, B6 untracked files, B7 lint result line, B8 every ERROR states its fix |

## 9. Gaps closed by this plan
| ID | Gap | Fill |
|---|---|---|
| GP1 | **Efficiency is measured only in the synthetic eval.** The retro of real sessions detects loops, heavy agents and big outputs, but not main calls, agents per change, inline residency, parallel factor or cost | The retro computes the headline KPIs of `eval/METRICS.md` from `events.jsonl` for every real delivery; the team sees the same numbers in production |
| GP2 | **No budget per change.** E17 brakes on time only | A token and cost budget by size in `state.md`; past it the main stops and reports (extends E17) |
| GP3 | **The interview is never measured** (the eval answers every question) | One scripted-user scenario that counts questions and their cost |
| GP4 | **Parallelism is never measured** (S5 to S7 are 1 to 2 tasks) | Scenario S8: a feature with three tasks, two independent |
| GP5 | **prd-create and trd-create** spawn mappers and writers without these rules | Same AG and CX rules, in a later round |
| GP6 | **The installer** must carry the new scripts, metrics and budgets | `/ai-kit update` and `doctor` (skill byte budget, missing scripts) |

## 10. Rounds (one change each)
| Round | Change | Must move | Cost |
|---|---|---|---|
| R0 | Hermetic eval (temp config dir, pinned model and effort), the new metrics, base and current head at 3 reps on S5 | a trustworthy baseline | about US$35 |
| R1 | Correctness (section 8) | `contradiction_left` 0, `conflict_recall` 1.0 | about US$25 |
| R2 | Agent map, main contract and spawn rule (AG1 to AG9, AG17, AG18), Promote ownership with `promote.py`, `gates.sh close`, CX4 | `main_calls` at most 30, `main_tokens_post_exec` at most 1.5M, agents per one-rule change at most 4, `dispatch_map` 1.0 | about US$25 |
| R2b | Parallel and context: AG10 to AG16, PX1 to PX5, CX1 to CX3, CX5, on S8 plus S5 to S7 | `parallel_factor` at least 1.5 on S8, S8 wall time, reads per agent, no Owns collision, S5 to S7 not worse | about US$30 |
| R3 | Instruction diet and doc budgets (CX7, CX8) | skill bytes read, `wall_min` | about US$25 |
| R4 | Friction (section 8) | `rework_actions`, error rate | about US$25 |
| R5 | Production telemetry and budget (GP1, GP2), no eval spend | the KPIs visible in the retro of real deliveries | none |

## 11. Decisions of the maintainer
| ID | Decision | Chosen |
|---|---|---|
| D1 | Step 6 | **Skipped when proven** (`--applied` green, no non-table changes); approval stays row by row at step 4; a flow rule change, recorded through the kit's catalog, SKILL.md and CHANGELOG in R2 |
| D2 | Strong model for surveyor and planner | **Every C5**, high effort where the platform allows it |
| D3 | Eval budget | **R0 to R2 first** (about US$85) |
| D4 | TRD merge at the end | **The last executor task**, TRD file in its Owns; `promote.py` does the rest |
| D5 | Execution session on the fast model after plan approval (CX6) | **Yes, as a measured arm in R2b**; adopted only if quality holds |
| D6 | Add R2b to the approved budget | **Yes: R0 to R2b**, about US$115 |
| D7 | Delivery mode (2026-10-08) | **Build everything in this plan, then one big evaluation** on every metric of `eval/METRICS.md`: arms prd-gate, prd-flow head, and prd-flow head with the fast-model execution session; S5 at 3 reps, S6, S7 and S8 at 1. Per-change attribution comes from the dispatch map, the main violations and the per-agent metrics instead of separate rounds. If the targets are not met, a full audit follows before any further change |

## Appendix: traceability of every finding of the conversation
| Source | IDs | Where it is handled | Status |
|---|---|---|---|
| First review | A01 to A15, B01 to B13, C01, C02 | PR #10 | done |
| Cost rounds | LS24 docs inline | AG1, AG2, AG9, AG19, `main_violations` | this plan |
| | LS25 free-form state files | gate HINT (done `641e905`); surveyor writes the scaffolds in the gate's format (C3) | this plan |
| | LS26 cold-start premise | reverted: Promote no longer folded blindly (D4 with explicit Owns plus `promote.py`), no SendMessage resume (AG6) | this plan |
| | LS27 rule argued away | numbers move to `rules/`; compliance enforced by AG19 and measured by `dispatch_map` | this plan |
| | Gate output flooding | scoped, capped, artifact | done `0e70861` |
| My audit | C1 turns, C2 main, C3 ceremony, C4 bloat, C5 cold starts, C6 formats, C7 bundled rounds | AG2, AG9, section 7, section 8 diet, AG19, AG12, Q5 and scaffolds, `eval/METRICS.md` | this plan |
| | S1 scripts | `promote.py`, `gates.sh close` (no other scripting layer, by the maintainer) | this plan |
| | S2 to S6 | section 7, section 8, AG12 and CX2, AG8 and AG19, D7 | this plan |
| Second audit | A1 Promote owner | D4, `promote.py`, plan check that every task with docs work owns those files | this plan |
| | A2 conflict | K14, Q5, rewrite format, surveyor strongest | this plan |
| | A3 reads before the surveyor | AG2 | this plan |
| | A4 SendMessage | AG6, AG17 | this plan |
| | A5 review policy | AG15, one table | this plan |
| | A6 size table, A7 deliveries path, A8 main load, A10 who runs `--rules`, A11 step 6, A12 diff reads | section 8, D1, AG2 | this plan |
| | A9 loops | AG5 | this plan |
| | B1 to B9 | section 8 | this plan |
| | C1 Promote, C2 close, C3 scaffolds | `promote.py`, `gates.sh close`, surveyor scaffolds | this plan |
| | EV1 hermetic, EV2 base and reps, EV3 blind metrics, EV4 interview | R0 work, `eval/METRICS.md`, GP3 | this plan (GP3 scripted user later) |
| Orchestration review | AG9 to AG19, PX1 to PX5, CX1 to CX8, MP1 to MP7, GP1 to GP6 | sections 4 to 6b, 9 | this plan |
| Flow review, round 1 | GP2 budget by size | deferred: the model cannot read its own token use mid-run, so a budget in `state.md` cannot be enforced; the retro of `gates.sh close` flags the overrun after the fact | deferred |
| | AG8 and D2 effort per agent | gap: the platform pins effort per session, not per agent; SKILL.md says planning sessions (steps 1 to 9) run at high effort, and the agents inherit the session's effort | gap recorded |
| | CX2 pack validity | the resume rule of SKILL.md: before step 5, a failing `git diff --quiet <pack Base> -- <pack paths>` dispatches a new surveyor | done |
| | PX5 isolation | `reference/execution.md` E22 | done |
| | Cleanup of `_gate`, `_tests`, `_close` | `reference/execution.md` E20: `gates.sh close` clears them with the slug's state after a passing close | done in the docs; the script side belongs to `close_gate.py` |
| | MP4 executor affinity by area | stated in `reference/agent-plan.md` | done |

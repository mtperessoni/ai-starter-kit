# Audit v5: prd-flow round 2026-10-08-big

Scope: 18 runs in `eval/results/2026-10-08-big/` (GATE, FLOW, FLOW-FAST; S5 x3, S6, S7, S8), their `.p2.jsonl` phase-2 sessions, `.review.json`, `.judge.json`, and the S7/S8 work trees still under `%TEMP%/ai-kit-eval/20261008-073305/`. Read-only audit; no kit file, metric code or run was changed.

## Verdict
The flow's design holds (no PRD or source read before the surveyor in any run, docs before code everywhere, conflict recall 1.0, parallel wave 1 in S8), but the verdict fails on four mechanical defects outside that design: executors write `Source:` lines promote cannot parse (8 of 12 runs, 51 main calls, 3.9M main tokens), the closing sequence duplicates what `gates.sh close` already runs (16 of 26 violations), a phase-2 session never loads the execution rules and reads the card field `Reviewer: none` as "skip the review" (both dispatch_map failures, one shipped Critical), and decisions that are not rule rows (contract, rollout) never reach the PRD, the executor or the reviewer (every prd_fidelity loss in S7 and S8). Several metrics are also still wrong (violations miss 37 real leaks, cost is split by model not by role, parallel_factor and wall_min are biased on S8).

## 1. Every main_violation (26 counted)

| Run | Count | What the main did | Real or false positive | Instruction that caused it |
|---|---|---|---|---|
| FLOW-S5-r1 | 3 | `gates.sh compare`, then `lint`+`ratchet`, then `docs`+`trailers`, all before `close` | Real: close runs the same five checks again | E18 "the full suite runs a single time, after all tasks" read as a separate step; the card's allowed list omits compare but does not forbid it |
| FLOW-S5-r3 | 2 | `compare`, `lint` before close | Real | Same |
| FLOW-S6-r1 | 1 | Read `docs/incoming/catalog-price-spec.md` before the surveyor (254 tokens) | False positive: it is the request itself; the card forbids PRD, TRD or source, the metric counts all of `docs/` | Metric `SOURCE_RE` |
| FLOW-S8-r1 | 5 | Wrote ADR 0001 and edited `docs/adr/README.md` (3 edits, 4 calls with the commit); `compare`; `lint/ratchet/docs/trailers` | Real | Surveyor return: "protected rule touched, right path is an ADR, confirm before closing"; no card line names who writes an ADR in a C5, so opus did it itself |
| FLOW-FAST-S5-r1 | 1 | `compare` in phase 2 | Real | Same as S5-r1 |
| FLOW-FAST-S5-r2 | 1 | `compare` | Real | Same |
| FLOW-FAST-S5-r3 | 3 | `compare`; hand edit of SHP-01 in `docs/prd/orders/03-shipping.md` (dropped the marker, filled Source); `gates.sh retro` | Real | Promote failed on Source lines; nothing says "promote failure goes to an agent"; Final asks for retro findings but close prints only the retro path |
| FLOW-FAST-S6-r1 | 3 | Read of the incoming spec (p1); `compare`; `retro` (p2) | 1 false positive, 2 real | As above |
| FLOW-FAST-S7-r1 | 1 | `compare` | Real | Same |
| FLOW-FAST-S8-r1 | 6 | `compare`; 4 hand edits of PRD rows in 03, 04, 05 (hand promotion after the Source error); `retro` | Real | As S5-r3 |

Summary: 9 `compare`, 4 other closing gates, 3 `retro`, 8 docs edits (3 ADR, 5 hand promotion), 2 false positives. 24 of 26 are real.

Real leaks the metric does not count (same 12 runs):

| Leak | FLOW | FLOW-FAST | Evidence |
|---|---|---|---|
| Source or diff content read after the surveyor (`git diff src/..`, `git show`, `Read src/..`, `sed -n` on source) | 4 | 5 | FLOW-S8 call 31 checks the reviewer's finding by hand; FAST-S7 p2 reads `checkout_flow.py` (7.7k chars) before committing; FAST-S6 p2 runs `git diff` on 3 files |
| Kit script reads (`promote.py` source, Grep of its regex) | 4 | 6 | Debugging the Source error, forbidden by "debugging the gate" |
| Edits of agents' files (`deliveries.md`, `impact.md`) | 7 | 2 | Rewriting Source lines; `STATE_RE` exempts the state folder |
| Retro reread (`cat retro.md`) | 3 | 6 | Every FAST phase 2 rereads it |

## 2. dispatch_map below 1.0 (FLOW-FAST S6 and S7)

| Fact | S6 p2 | S7 p2 | Other 4 p2 sessions |
|---|---|---|---|
| Skipped step | prd-flow-reviewer | prd-flow-reviewer | reviewer dispatched |
| Skill loaded in phase 2 | yes (Skill call) | no (first call Read state.md; context 35k, no 3k card) | 1 of 4 |
| `execution.md` or `review.md` read in phase 2 | no | no | no (0 of 6) |
| Plan card field | `Reviewer: none` | `Reviewer: none` | `Reviewer: none` (all 12 plans) |
| Main's stated reason | "The plan says Reviewer: none so I skip the wave reviewer" | "T01 has no reviewer per the plan" | |
| Consequence | none found (blind review clean) | blind Critical (VIP exempted from the 30.00 minimum) and High (check skipped with a coupon) shipped | |

Cause: not lost context but a missing rule in the context it kept. `state.md` (the only file a resume must read) holds the wave table but no execution steps; the field `Reviewer:` in the card format (agent-plan.md) means "lens from repo.md", while E06 says every wave is reviewed. Opus resolved the ambiguity from the step-10 text it had loaded; sonnet, without the card or E06, took the field literally. The phase-2 prompt (`prompt-phase2.md`) also drops the "reviewer at the end of each wave" paragraph that `prompt.md` carries in phase 1.

## 3. Where the main calls and tokens go

Per phase, summed over the 6 runs of each arm (calls / main tokens). Phase boundaries: surveyor dispatch, docs dispatch, first executor, first `compare|promote|close`.

| Phase | FLOW | FLOW-FAST | Main content of the phase |
|---|---|---|---|
| Before surveyor | 40 / 1.92M | 34 / 1.63M | Skill, 3 reference reads (repo, classification, interview: 22.6k chars), INDEX Grep, `gates.sh context` (retried in 3 runs), mkdir, state.md write, python probe |
| Interview | 56 / 3.67M | 49 / 3.18M | 4 to 6 separate reads of impact, approved-rules, interview, decisions; 4 to 6 separate writes; `gate.py --rules`; state.md edit |
| Docs and plan approval | 26 / 1.95M | 28 / 2.05M | Plan read, git status/log, state.md edit, commit of the main's own files |
| Phase-2 restart | n/a | 32 / 1.30M | Read state and plan, Glob, python probe, baseline (cheap: 35k to 45k context, sonnet) |
| Execution | 52 / 4.45M | 54 / 2.67M | Dispatch, git status + diff --stat + log per return, commit, state.md per wave, diff reads |
| Closing | 70 / 6.64M | 65 / 3.71M | compare, lint, promote failure and recovery, commit, close, retro |
| Total | 244 / 18.6M | 262 / 14.5M | GATE: 262 / 23.9M, 9.7M after the first executor |

Average context per call: FLOW 76k, FLOW-FAST 55k (phase 2 starts at 35k). Closing is the most expensive phase in FLOW (36% of main tokens).

Top 5 avoidable clusters (FLOW and FLOW-FAST together, 12 runs):

| # | Cluster | Calls | Main tokens | Runs | Avoidable share |
|---|---|---|---|---|---|
| A | Promote Source failure: rerun, read `promote.py`, rewrite `deliveries.md` or hand-edit PRD rows | 51 | 3.91M | 8 of 12 | all |
| B | Interview bookkeeping split one file per call (reads and writes of 4 state files, state.md edits) | 71 | 4.6M | 12 | about half (batch reads in one message, writes in one message, confrontation in the surveyor's return) |
| C | Post-return verification: `git status`, `git log`, `git diff --stat`, then diff content, then a separate commit | 62 | 4.0M | 12 | about 60% (one Bash: `git diff --stat -- <files> && git add && git commit`) |
| D | Duplicate closing checks (compare, lint, ratchet, docs, trailers, retro, `cat retro.md`) | 22 | 1.58M | 12 | all |
| E | Setup before the surveyor (context retry, mkdir, state.md write, python probe, classification.md read) | 28 | 1.46M | 12 | about 60% (surveyor creates the folder and decides the case) |

## 4. S8: why it is slow

| Question | Answer from the transcripts |
|---|---|
| Did the plan produce 2 waves? | Yes in both arms: WAVE 1 T01 (loyalty), T02 (shipping); WAVE 2 T03 (checkout wiring). Granularity matched the rule and `expected_waves` 2 |
| Were wave-1 tasks dispatched together? | FLOW: one message, foreground; FAST: two messages, background. Both overlapped: FLOW T01 12.5 to 14.1 min, T02 12.6 to 13.9 |
| Why parallel_factor 0.74? | The metric divides executor minutes by the window from the first executor start to the last executor end; that window contains the wave-1 review (1.0 min), the fix and recheck (FLOW 1.1 min) and wave 2 (serial by design). GATE reviews once after all waves, so its window holds only executors (1.13). With 3 tasks in 2 waves and a review between them, 1.5 is not reachable |
| Why 7 to 9 cold starts? | FLOW: surveyor, docs, T01, T02, reviewer W1, fix, recheck, T03, reviewer W2 = 9. FAST: no fix/recheck = 7. GATE: 3 executors and 1 reviewer = 4 (planning inline in the main, 61 violations) |
| Where do the 25.4 min (FLOW) go? | surveyor 1.0 to 3.6; interview 3.6 to 6.5 (incl. 4 calls writing an ADR); docs 6.5 to 11.6 (57 calls, 2.0M tokens, opus, size L with brief and design); wave 1 12.3 to 14.1; review, fix, recheck 14.4 to 17.7; T03 on opus 17.9 to 20.7 (789k tokens); review 21.0 to 22.4; closing 22.9 to 25.4 (8 calls of promote recovery). GATE starts executors at 8.2 min |
| Why the fix round in FLOW? | The fixture has `>` where SHP-02 says "200.00 or more". The surveyor flagged it as an out-of-scope divergence; the card did not carry it; T02 silently changed it to `>=`; the reviewer called that a stealth change; the main read the diff itself and dispatched a revert. The blind review then flagged the reverted `>` as High. Cost: 2 cold starts, about 3.5 min, first_pass_rate 0.667 |

## 5. Code and PRD quality

| Run | Blind review | Caused by |
|---|---|---|
| FLOW-FAST-S7 | Critical: VIP exempted from the minimum; High: check skipped when a coupon is present; Medium test gap | Flow: no reviewer in phase 2 (section 2); the executor turned the open question Q-CHK-08 into an exemption, an R09 case the executor rule forbids |
| FLOW-S7 | High: new public `BelowMinimumOrderError` against DEC-03 "no new public name"; 2 Medium test gaps (VIP, coupon) | Flow: DEC rows live only in `decisions.md`; the executor reads rule rows and the reviewer reads the diff plus rule rows, so neither sees DEC-03 |
| FLOW-S8 | High: `>` at 200.00 | Mostly noise from the fixture divergence (all 5 S8 trees end with `>`, only this diff exposed the line); the flow cost is the fix cycle in section 4 |
| FLOW-FAST-S8, GATE-S8 | one Low each | noise |

| Judge fact missing | Runs | Where the fact went | Flow or noise |
|---|---|---|---|
| S7 f4, S8 f5: "applies to every order from now on, no flag, no migration" | FLOW and FAST, S7 and S8 (GATE wrote it in S7) | Interview D13 transition answered `assumed-confirmed` in `interview.md`, which close deletes; not in PRD, not in DEC rows | Flow, deterministic |
| S8 f4: "receipt layout and `as_dict` do not change" | FLOW and FAST | Interview D08 contract row; GATE wrote it as CHK-09 | Flow, deterministic |

Also deterministic: every FLOW run has two CHANGELOG entries for the same change (docs agent writes one at step 5 per prd-writing.md, `promote.py` appends a second), which doubles the DEC rows and inflates `single_source` (17.5 and 18 against 12.5).

## 6. Measurement validity

| Metric | Problem | Effect in this round |
|---|---|---|
| `main_violations` | Counts the request document under `docs/incoming/`; misses diff and source reads after the surveyor, kit-script reads, edits of agents' files, retro rereads | 2 false positives; 37 real leaks unseen |
| `cost_main_usd`, `cost_subagents_usd` | Split by model, not by role: opus surveyor and docs count as main; in FAST every subagent shares its session's model | FAST `cost_subagents_usd` 0 in S5 to S7; FLOW main cost overstated by the 9.6M opus subagent tokens |
| `wall_min` (two-phase, background agents) | Taken from the last `result` event's `duration_ms`; FAST-S8 p2 has 3 results (81 s, 3 s, 438 s) because the main ended its turn while agents ran | FAST-S8 wall undercounted by about 1.4 min (19.7 is about 21.1) |
| `parallel_factor` | Window includes reviews and serial waves; target 1.5 unreachable for S8's shape | 0.74 does not mean "no parallelism" |
| `waves`, `tasks_per_executor` | A fix executor opens a new wave and counts as an executor | FLOW-S8 waves 3 for a 2-wave plan |
| `traceability` | `prd_diff_ids` takes any `XXX-NN` first cell, including `DEC-01` rows of the CHANGELOG | FLOW S7 0.2 is 1 of 5 where 4 are DEC rows; real value 1.0 |
| GATE-S7 | GATE did no code (accept 0.571) | Total time 78.2 against 98.9 is not like for like; without S7: GATE 70.5, FLOW 86.0, FAST 73.8 |
| Hermetic setup | Verified hermetic: fresh `CLAUDE_CONFIG_DIR`, `--setting-sources project,local`, 0 MCP servers, no RTK or operator text in any transcript. The 34k start is 21.3k Claude Code base (identical cached prefix in all arms) + about 8.5k fixture CLAUDE.md, AGENTS.md, skill and agent listings + about 4k prompt. Auto-memory is still on: FLOW-S5-r2 spent 2 calls writing memory files | No operator leak this round; auto-memory is noise worth turning off |
| Variance (S5, 3 reps) | FLOW tokens_main spread 0.66M: r1 had 9 promote-recovery calls (0.80M), r2 had 3 (0.25M). FAST spread 0.74M: r2 split a one-rule change into 2 tasks (+1 executor, +5 calls) and 9 recovery calls. GATE cost spread 0.294 on 0.752 (39%) | The -18% FAST S5 cost is inside GATE's own spread: suggestive, not proven |

## 7. Is FLOW-FAST the better default?

| Evidence for | Evidence against (risk) |
|---|---|
| Cost $30.2 against FLOW $36.0 (-16%), equal to GATE $30.3; main tokens 14.5M against 18.6M (-22%) | Phase 2 never read `execution.md` or `review.md` (0 of 6) and did not load the skill in 3 of 6 |
| Phase 2 costs $0.85 to $2.71 per run; the opus phase 1 is 59% to 79% of the cost | Reviewer skipped in 2 of 6; a Critical shipped in S7 |
| Wall 86.3 against 98.9 min; S8 19.7 (about 21.1 corrected) against 25.4 | Hand promotion of PRD rows in 2 of 6 (a docs edit by the main) |
| Same hidden-test result (45 of 45), conflict recall 1.0, rework 16 against 14 | Phase-2 sonnet read source to "verify" in 3 of 6 |

Answer: yes as the default shape (plan on opus, execute in a fresh sonnet session), because the saving comes from the fresh 35k context as much as from the model, and both are structural. Not before fixes 1 to 3 below: today the execution session depends on rules it never loads.

## Ranked fixes

| # | Fix (agent management and context first) | Cause removed | Metric it moves | Expected effect | Effort |
|---|---|---|---|---|---|
| 1 | Executor writes one `Source: <ID>: <path::symbol>` line per approved code rule its Owns implement, rewritten rules included, never a list or a range; show a two-ID example in `prd-flow-executor.md`. Cheap guard: let `promote.py` split `A, B` and `A..C` | Promote failure, 8 of 12 runs | main_calls, tokens_main, main_violations, wall | -4.3 calls and -0.33M main tokens per run on average (-6.4 calls, -0.49M where it fails); removes 5 PRD hand edits | S |
| 2 | Make resume self-sufficient: SKILL "resume" lists the execution steps (baseline, per wave: dispatch, commit, `prd-flow-reviewer` always, recheck after a fix, promote, close); docs agent copies those 6 lines into `state.md`; rename the card field `Reviewer:` to `Lens:`; phase-2 prompt keeps the reviewer paragraph | Reviewer skipped, skill not loaded | dispatch_map, review_weighted, blind Critical | dispatch_map 1.0 in FAST; removes the S7 Critical and High | S |
| 3 | One closing command: card forbids compare, lint, ratchet, docs, trailers and retro in the main; `gates.sh close` prints the retro findings (at most 5 lines) so Final needs no read; a failing close goes to an executor with the failure lines | Duplicate checks, retro rereads | main_violations, main_calls, wall | -16 counted violations (62%), -1.8 calls and -0.13M per run, about -1 min | S |
| 4 | Owner for every docs write: ADR goes to the docs agent at step 5 when the surveyor flags a protected rule; a promote error goes to an executor (Source) or docs `fold`, never to the main | Main writing ADR and PRD rows | main_violations | -8 counted violations | S |
| 5 | Batch bookkeeping: read the surveyor's state files in one message, write the four interview files in one message, carry the confrontation in the surveyor's return (no impact.md read), surveyor creates the state folder and decides the case (drop classification.md and mkdir from the main) | Clusters B and E | main_calls, tokens_main, start-to-surveyor | -6 to -8 calls and -0.5M per run; FLOW S8 within 3.5M | S |
| 6 | Commit in one Bash per return (`git diff --stat -- <files> && git add <files> && git commit -F -`), no status, log or diff content; the reviewer is the only reader of the diff; state.md cost line appended in the same command | Cluster C, uncounted diff reads | main_calls, tokens_main, hidden violations | -3 calls and -0.25M per run | S |
| 7 | Carry decisions that are not rows: the docs agent turns D08 (contract) and D13 (rollout) answers into a PRD line or row; the card lists `Decisions: DEC-nn` and executor and reviewer read those rows; the card lists the surveyor's out-of-scope divergences under `Leave:` | Missing facts, DEC-03 miss, S8 fix cycle | prd_fidelity, review_weighted, cold_starts, wall S8 | S7 0.75 to 1.0, S8 0.6 to 0.8 or 1.0; -2 cold starts and about -3 min in S8 | S |
| 8 | One CHANGELOG entry: promote completes the step-5 entry (excerpts, Source) instead of appending a second | Duplicate entry | single_source, traceability | single_source back near GATE; DEC rows once | S |
| 9 | Model and read discipline: `Model: opus` only for a new safety decision (drop "serial chain, big file" from agent-plan.md, matching E13); docs agent reads `pack.md`, not source (8 source reads in S8) | T03 on opus (789k), docs agent 39 calls a run | cost, wall S8, tokens_subagents | about -0.5M opus tokens and -1 min in S8; docs agent -8 calls | S |
| 10 | Metric fixes in `protocol.py`, `transcript.py`, `grade.py`: violation categories above, cost by role, wall from summed results, parallel_factor over executor segments only, fix dispatches not waves, DEC/Q rows out of traceability, auto-memory off in the harness, S8 target revised; then 3 reps of S7 and S8 | Wrong scores | all hard gates | Verdict reflects the flow, not the metric | M |

Fixes 1 to 7 are card, agent-file and prompt changes; only 1 (optional guard), 3 (retro lines) and 8 touch scripts, each in a few lines.

# Audit: prd-flow cost, time and quality (branch `fix/prd-flow-cost`)

Date: 2026-10-07. Evidence: the transcripts of `eval/results/2026-10-07-flow*` (GATE, FLOW r1 to r4; r4 is the head of this branch, S5 at 2 reps), the skill files, the gate scripts (97 gate tests green) and the docs that feed the flow. Every number below comes from those transcripts. Prices were derived from `modelUsage`, and they reproduce `total_cost_usd` to the cent: Opus main thread input 5, output 25, cache read 0.5 and cache write (1 h TTL) 10 USD per million tokens; Sonnet workers read 0.3 and write (5 min TTL) 3.75.

## 1. Verdict

The head of the branch is not cheaper than r3, and it is about 75% more expensive than prd-gate per run.

| Arm | Runs | Cost per run (USD) | Wall per run (min) | Hidden tests | `contradiction_left` (S5) |
|---|---|---|---|---|---|
| GATE (prd-gate) | 3 (one sample reused in every round) | 3.84 | 10.9 | 19/22 | 1 |
| FLOW r3 | 3 | 6.54 | 18.9 | 22/22 | 1 |
| FLOW r4 (head) | 4 | 6.75 | 18.8 | 29/29 | 1 in both reps |

The quality gains of prd-flow are real: every hidden test passed, and S7 was completed. The cost comes from four structural causes, and none of them is the docs phase that rounds 2 to 4 tried to optimize:

1. **The Opus main thread does the work after the executor.** In r4, 53% to 66% of main-thread tokens were spent after the first executor dispatch: Promote inline, diff reading, gate debugging, lint and closing ceremony. That cost 2.6M to 3.5M context tokens per run, against 1.8M in GATE.
2. **Self-contradictory instructions,** which the model resolves by doing the work inline (section 3, A1 to A6).
3. **Gate and environment friction** that turns one command into a 3 to 6 turn detour (section 3, B1 to B8).
4. **The eval cannot see protocol regressions.** `protocol_adherence` is 1.0 in every run of every arm, `docs_dispatched` ignores the surveyor and Promote, the base arm is n=1, and the environment is not hermetic (section 4).

## 2. Where the money goes (r4, S5 rep 1, USD 6.76, 20.2 min)

| Thread | Calls | Context-weighted tokens | Cost | Minutes |
|---|---|---|---|---|
| Main, before the executor | 21 | 1.42M | ~1.3 | ~4 |
| Main, after the executor | 34 | 3.54M | ~3.2 | ~5.4 |
| surveyor (Sonnet) | 17 | 0.69M | ~0.30 | 2.1 |
| writer-prd | 16 | 0.52M | ~0.22 | 1.6 |
| writer-trd + planner | 21 | 0.76M | ~0.33 | 1.8 |
| executor | 35 | 1.37M | ~0.58 | 4.3 |
| reviewer x2 | 10 | 0.30M | ~0.13 | 0.9 |

Main-thread cost split: cache reads 54%, cache writes 24% (every new token enters the 1 h cache at USD 10/M), output 20%. Starting context is 39k tokens before the skill loads, and every worker starts at 23k. One main call at about 100k context costs about USD 0.08, so **main-thread call count is the lever**: r4 makes 50 to 55 main calls per C5, GATE made 25 to 38.

Over seven r3 and r4 runs, the main thread ran `gate.py` 33 times (the skill allows once), `build_prd_html` 19, `git diff` 23 and `git commit` 25. It read source code 8 times and the gate's own source 4 times, `reference/interview.md` 7 of 7 times and `reference/execution.md` 5 of 7 times.

LS26's premise ("each agent pays a cold start of about a minute") does not hold in the data: a scoped re-review agent took 0.1 min, and agent minutes are work. The two changes built on it, Promote folded into the last code task (`ede5753`) and the docs agent resumed with SendMessage (`5409e23`), are the two largest regressions of r4.

## 3. Findings

Severity: Critical = wrong product output, High = repeated cost or rework in most runs, Medium = occasional detour, Low = noise. "Seen" names the runs where the transcript shows it.

### A. Skill instructions (cause inline work and protocol drift)
| ID | Sev | Finding | Evidence | Fix |
|---|---|---|---|---|
| A1 | High | Promote has no owner. The plan folds it into T01 while T01 says "Does not touch: `docs/`, `changes/`". executor.md has no Promote steps, the Promote block has no Owns/Model/Commit (`gate_plan.py:24` exempts it), and SKILL.md:54 says "always dispatched" while agent-plan.md:83 says "fold". | r4 S5 x2 and S7: executor skipped it, reviewer flagged it, main did 10 to 15 Opus edits at 110k to 130k context (~USD 1 to 1.3 per run). S6 dispatched Promote as its own agent: 0.72M Sonnet, ~USD 0.35 | Revert the fold. Promote is always its own task with explicit Owns (`docs/prd/**`, `docs/trd/**`, `changes/NNN-*/**`, the HTML), Model sonnet and a commit; better, a script (C1) |
| A2 | Critical | The conflict check misses an unconditional rule that the new rule makes false. K11 says "contradict, constrain or duplicate" and never names this case. No format rewrites an existing row (same ID, new text): prd-writing says never reuse an ID, and a superseded row stays live | r3 and r4 S5 (3 of 3 runs): the surveyor wrote "SHP-01 unchanged… No further conflicts found" next to "Shipping costs 15.00."; the PRD ships with two rules that disagree | Add K14: "a row stated without condition that the new rule makes false for some input is a conflict; it is rewritten in the same row". Define the rewrite format (same ID, same file, old text under `## Supersedes` as `ID: old text`). Gate check: a row whose Source matches a new rule's Planned file must be re-approved or listed as `compatible: <reason>` in impact.md. Run the surveyor on Opus for every C5 (+~USD 0.2) |
| A3 | High | Nothing in the C5 route forbids the Light-route reads. The main reads PRD sections, TRD and code before the surveyor (which rereads them), then reasons "I hold full context" and skips the surveyor | r4 S6 and S7: no surveyor; S7 main wrote impact and interview inline, citing R04 ("interview runs here") as if it covered the confrontation; 14.4 of 22.3 min were main-only | C5 step 1: read only `repo.md` and one Grep of INDEX; "no PRD tables, TRD or source before step 2". R04 says "interview", not "confrontation" |
| A4 | High | "Resume the same agent with SendMessage" is testable only by searching. SendMessage is deferred, so the main calls ToolSearch, which rewrites the cache | r4 S6: 85k, S7: 69k tokens rewritten at USD 10/M after ToolSearch; every r4 run fell back to a new agent anyway | Default to one new agent for steps 7 and 8. Resume only if SendMessage is already in the tool list; "never ToolSearch for it" |
| A5 | High | Review policy contradicts itself: E06 says "every wave, one-task included", while repo.md and agent-plan put `Reviewer: none` in the plan. The counter is per delivery but rounds run per wave; an open Critical at round 5 cannot close (its fix has no re-review) | r4 S6: "Reviewer is none per repo.md", no review. S7 reviewed only because the eval prompt forces it | One table: every wave of a C5 gets one review round; round 2 only if Critical/High was fixed; Medium/Low go to pending without re-review; the round-5 fix gets a scoped check that is not round 6 |
| A6 | Medium | The size table lives only in classification.md, which the main reads "only when in doubt". It labels C5 as "size S", which does not exist for C5, and the surveyor sweep depends on size | r4 S5, S6 ("C5, size S"); S7 switched S then M | Three lines in SKILL.md: C5 is M or L, with the L triggers |
| A7 | High | `deliveries.md` is written bare in 4 places; only SKILL.md:61 says state folder, and the next sentence says plans live in `changes/` | r4 S5: executor wrote it into `changes/`; main moved it (one extra call); otherwise it gets archived as truth | Full path `.claude/prd-flow/state/<slug>/deliveries.md` everywhere |
| A8 | Medium | The main thread loads 44 KB of skill text (SKILL, repo, interview, execution, review, classification); steps 1 to 9 need about 28 KB. E12 to E19 and about 5 KB of repo.md are worker-only. The formats of step 4 are written twice (SKILL.md:56-58 and interview.md) | interview.md read 7/7, execution.md 5/7 | A "Main thread" card in SKILL.md with the step-4 formats and the step-10 loop (about 15 lines); execution.md and review.md become worker-side |
| A9 | Medium | Unbounded fix loops: "fix and run again" in surveyor, writer-prd, writer-trd and the main's step 4 ("until it passes") have no cap; E17 brakes only execution | r2: 47 gate runs in workers (format loop) | "At most 2 reruns per step; the third failure returns the ERROR lines as a gap" |
| A10 | Medium | Who runs `gate --rules` is contradictory: SKILL.md:16,46 (main, once, until green) versus rules/07 WF53 (main never). writer-prd reruns the same check at its step 1 | 3 runs of the same check per C5 | The main runs it once; writer-prd reads the result line from `state.md` |
| A11 | Medium | Plan approval and the step-6 PRD confirmation make the main open the plan (4 to 5 KB) and `git show` the PRD commit, although the rows were approved literally at step 4 and Q4 proves the literal copy | Every run | Step 6: show the gate line and non-table changes only; step 9: approve from the planner's table. Proposal for the user (a rule change): drop step 6 when `--applied` is green and there are no non-table changes, so one docs agent does PRD, TRD and plan |
| A12 | Medium | E05 makes the main read the executor's diff before committing; the reviewer reads it again | r4: 2 to 3 diff reads per task at 100k+ | E05: `git diff --stat` against the returned file list; content belongs to the reviewer |

### B. Scripts (one command becomes a 3 to 6 turn detour)
| ID | Sev | Finding | Fix |
|---|---|---|---|
| B1 | Critical | `gate.py --base <missing ref>` prints `gate:0 error(s)` and exits 0 (`gate_output.py:22`; `gate_core.git` drops stderr) | `git rev-parse --verify`; ERROR when the base is missing |
| B2 | High | Without `origin/<base>` the base silently becomes HEAD: G7 is red before a commit and green after it, and `--step trd` parks every TRD error as a warning | Fall back to the local base branch; otherwise WARN "no base, results change after commit" |
| B3 | High | G7 fires when Promote only removes the `*(approved …, pending code)*` marker, and the message gives no remedy; any CHANGELOG touch silences G7 for every other rule (`gate.py:93`) | Strip marker tokens before comparing; require an added CHANGELOG line with the ID; say so in the message. Seen in r4 S5 and S7: the main read gate source to understand it |
| B4 | High | `gates.sh trailers` uses the literal `origin/<base>..HEAD` (`commit_trailers.py:72`) and `related_tests.py:177` hardcodes `origin/main` | One base resolver for all scripts (origin/X, then X, then "pass a range"). Seen in every r4 run |
| B5 | High | `build_prd_html.py` is cited as bare or `scripts/…` in repo.md:31, agent-plan.md:76, AGENTS.md:25, rules/06:70 and its own `--check` hint (`build_prd_html.py:386`); the real path is under the skill | Full path everywhere plus `gates.sh html`. Seen: wrong path then Glob in 5 of 7 runs |
| B6 | High | G23 says "matches no tracked file" for a new untracked source file (`gate_trd.py:19,78`, `ls-files` without `-o`) and never says `git add` | `ls-files -co` and a hint |
| B7 | Medium | `gates.sh lint/fix/imports` print nothing on success and have no exit line; with the RTK proxy the executor retried lint 5 times (bash, `cat /tmp`, PowerShell) | Always print `lint ok|FAILED (exit N), log <path>` |
| B8 | Medium | 20 ERROR messages state no fix (G1, G3, G5 to G8, G10 to G12, G15, G16, G19, G22, G23, G28, P1, P2, P5, Q1, Q4); Q4 shows no diff of the differing cell | Every ERROR ends with "fix: …"; Q4 prints both cells |
| B9 | Medium | Warnings and errors share the cap and the "… N more" line; a TRD broken by a moved file the change did not edit is parked as a warning | Separate counts; an error when the cited path is in the diff |

### C. Missing automation (deterministic work done by the most expensive model)
| ID | Sev | Finding | Fix |
|---|---|---|---|
| C1 | High | Promote is mostly mechanical (drop markers, set Source from the TRD Planned row, CHANGELOG literal excerpt, HTML rebuild, `git mv` archive, `gate --final`) | `promote.py <slug>` does all of it except the TRD Planned merge, which goes to a Sonnet task |
| C2 | High | Closing ceremony: compare, lint, trailers, `gate --final`, retro and `git status` take 6 to 8 main calls at 115k to 130k | `gates.sh close <slug>`: one call, one summary block |
| C3 | Medium | Step 4 scaffolding: state.md, interview.md with D01 to D15 plus extras, approved-rules skeleton, decisions.md from the template, next change number | The surveyor writes them already in the gate's format (it has every dimension in its pre-interview); the main only edits States and rows |

## 4. The evaluation itself

| ID | Sev | Finding | Fix |
|---|---|---|---|
| EV1 | High | Not hermetic: `claude -p` loads the operator's `~/.claude` (global CLAUDE.md with overlapping subagent rules, 32 personal skills, the RTK Bash hook that swallowed lint output, memory, `effortLevel: high`, model `opus[1m]`). The main starts at 39k tokens | Run with a temp `CLAUDE_CONFIG_DIR` (or `--setting-sources project,local`) and pin `--model`; record the starting context as a metric |
| EV2 | High | The base arm is one run copied into every round, and each round changed 2 to 4 things at once with one rep, so no change can be attributed | Rerun the base each round; 3 reps on the deciding scenario; one change per round, or an ablation arm per change |
| EV3 | High | Protocol metrics are blind: `protocol_adherence` only checks the skill was invoked (1.0 everywhere); `docs_dispatched` matches `writer|planner` only | A dispatch map per run (surveyor, writer-prd, writer-trd, planner, executor, reviewer, promote) and main-thread violations (below) |
| EV4 | Medium | The unattended prompt answers every question, so the interview, the real per-question cost at 80k+ context, is never measured | One interactive-simulated scenario with a scripted user, or an `AskUserQuestion` count from a replay |

## 5. Metrics for the next rounds

One scorecard per run, computed by `eval/run.py`, compared with `eval/rounds.py`. New fields are marked **new**.

| Group | Metric | Definition | Target for a C5 size M (S5) |
|---|---|---|---|
| Cost | `cost_per_accept` | `cost_usd / accept` | at most 4.5 USD |
| Cost | `main_calls` **new** | unique main-thread API calls | at most 30 |
| Cost | `main_tokens_post_exec` **new** | main context tokens after the first executor dispatch | at most 1.5M |
| Cost | `main_cache_write` **new** | main cache-write tokens; flags cache busts (above 30k in one call) | no bust |
| Time | `wall_min`, `main_only_min` **new** | wall time and wall minus agent intervals | at most 15 and at most 6 |
| Success | `first_pass` **new** | accepted with no review fix, no gate rerun after a fail, no re-dispatch | true |
| Rework | `rework_actions` **new** | gate fails + review fix rounds + test/lint retries + re-dispatches | at most 2 |
| Rework | `max_reruns_per_step` **new** | loop detector: the same gate step or command repeated | at most 2 |
| Quality | `hidden_passed`, `contradiction_left`, `conflict_recall` **new** (expected conflict IDs named in impact.md) | behavior correct, PRD consistent, conflict found by the surveyor | all, 0, 1.0 (hard gates) |
| Quality | `prd_fidelity`, `traceability` | judge facts; IDs cited in code and tests | at least the base |
| Code quality | `review_weighted` **new** | blind findings weighted Critical 8, High 4, Medium 2, Low 1, per 100 changed lines; ratchet and lint green | at most the base |
| Review need | `review_rounds`, `findings_by_severity` | rounds used and why | at most 2 |
| Protocol | `dispatch_map` **new** | each step dispatched (bool); compliance = fraction | 1.0 (hard gate) |
| Protocol | `main_violations` **new** | main edits under docs/ or src/, main reads of source, extra main gate runs, worker-only references read | 0 |

Adoption: hard gates are `hidden_passed`, `contradiction_left = 0`, `conflict_recall = 1` and `dispatch_map = 1.0`; then the median of 3 reps on S5 within +10% of the base on `cost_per_accept` and `wall_min`; a metric outside the noise band (the spread of the 3 reps) counts as a win or a loss.

## 6. Order of work

Each step names the metric it should move; measure after each wave, not at the end.

| Wave | Items | Expected effect per C5 run |
|---|---|---|
| 1 Eval first | EV1, EV2, EV3, the new metrics | Numbers that can attribute a change; no skill change before this |
| 2 Correctness | A2 (conflict check and rewrite format), B1, B2, B3 | `contradiction_left` 0; no false-green gate |
| 3 Main-thread diet | A1 + C1 (Promote owned, scripted), C2 (`gates.sh close`), A3, A4, A12, A8 | main calls from about 52 to about 28; about USD 2 and 4 to 6 min less |
| 4 Friction | A5, A6, A7, A9, A10, B4 to B9, C3 | tool errors from about 6 to at most 2 per run; no loop above 2 reruns |
| 5 Rule change (needs a person) | A11: drop step 6 when the literal copy is proven, one docs agent | one agent and 2 to 3 main calls less |

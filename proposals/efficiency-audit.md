# Efficiency audit of prd-flow

Date: 2026-10-08. Sources: the 16 eval transcripts of `eval/results/2026-10-07-flow*` (prd-gate and four prd-flow rounds), `eval/rounds.py`, timing of the scripts on a real repository (agora-consulta-fe, 161 rules), and the size of every instruction file. Numbers are medians per run unless stated.

## Verdict
prd-flow is slow and expensive because it is **turn-heavy on the most expensive context**, not because of scripts or context flooding. A one-rule change takes about 140 model turns (prd-gate: about 65); every turn of the main thread resends 80k to 95k tokens on the strongest model; and the ceremony per change is fixed, so a small change pays the same as a large one. Each round added instructions to fix the previous round, so the skill grew 44% and every new sentence became a new way to fail.

## What it is not
| Suspect | Measured | Verdict |
|---|---|---|
| Slow scripts | `gate.py` 1.1 s, `--step trd` 1.3 s, `--status` 0.1 s, `build_prd_html.py` 0.15 s | Not the cause |
| Gate output flooding | Was 44 lines per `--trd` run on a real repo; now 4 (scoped, capped, artifact) | Fixed, minor |
| Prompt cache | Hit rate 0.94 to 0.97 in every run | Healthy |
| Output verbosity | Output tokens under 1% of total | Not the cause |

## What it is
| # | Cause | Evidence | Effect |
|---|---|---|---|
| C1 | **Turn count.** Every action (git status, a commit, reading a state file, a gate run) is a model turn that resends the whole context | Turns per run: prd-gate about 65 (31 main + 34 in agents); flow r4 about 140 (47 main + 93 in agents). Bash calls per run: git 8 to 20, tests 9 to 12, gate 2 to 10 | Wall time and cost scale with turns: about 2.2x the turns, about 2x the time |
| C2 | **The main thread is the expensive part.** It runs on the strongest model with the largest context | Main context per turn 81k to 94k; first turn already 39k (system prompt, tools, CLAUDE.md, AGENTS.md). Main share of cost: 55% (r2) to 80% (prd-gate) | One extra main turn costs as much as several agent turns |
| C3 | **Fixed ceremony per change.** Surveyor, 15-row interview table, approved-rules, decisions.md, pack.md, writing.md, deliveries.md, state.md, gate per step, HTML build, CHANGELOG, Promote, archive, review rounds, for a one-rule change as for a new feature | 5 to 6 agents and about 140 turns for one rule (S5); cold starts per run 5 to 6 | The flow does not scale down |
| C4 | **Instruction bloat.** Skill text grew from 57 KB to 82 KB (+44%); SKILL.md 9.5 to 13.8 KB; interview, impact and prd-writing +80% | Skill files read per run: prd-gate 2, flow r2 to r4 22 to 25. Agent cold start 23k tokens before work | More to read on every agent, more rules ignored |
| C5 | **Cold starts.** Each agent rebuilds context from zero | 23k tokens and about a minute each; reads per agent 6 (prd-gate) to 12 (r4) | 5 to 6 per change |
| C6 | **Strict formats without a single writer of them.** The gate parses state files the model writes by hand | r2: 47 gate runs inside agents (format loop); r3 and r4: a format sentence made the conflicting rule drop out of approved-rules.md (S5 contradiction) | Retry loops and a quality regression |
| C7 | **Patching instructions, many at once, one rep.** r3 and r4 each changed four to six things | Contradiction came back in r3 with no way to attribute it from the round; one inline-versus-dispatch choice swings a run by US$2 to 3 | Whack-a-mole: every fix opened a new failure |

## What to change (structural, not more sentences)
| # | Change | Targets | Expected |
|---|---|---|---|
| S1 | **Mechanical steps become scripts, not turns.** `flow.py commit <task>` (diff check, file list, trailer, commit), `flow.py promote <slug>` (remove markers, fill Source from deliveries, move superseded text to the CHANGELOG, fold, rebuild HTML, archive, `gate --final`), `flow.py state <slug>` (write and validate the state files from a short answer list) | C1, C2, C6 | Main turns per change from about 47 to about 15; the Promote agent and its retries gone; no hand-written formats |
| S2 | **Ceremony by size.** S and M with one rule: one docs agent (survey, PRD, TRD, plan in one context) between the confrontation and the code; interview only the dimensions the change touches; no brief, no pack separate from impact, no writing.md. L keeps the full route | C3, C5 | Agents per small change from 5 or 6 to 2 or 3 (docs, executor, reviewer) |
| S3 | **Instruction diet with a budget.** SKILL.md at most 6 KB, imperative only; the "why" and the measured numbers live in `rules/` and the lessons, never in runtime files; every reference read by one role only; a ratchet on skill bytes | C4, C7 | Skill reads per run back to single digits; fewer ignored rules |
| S4 | **Context packs instead of exploration.** The planner writes, per task, the exact files and symbols to read; the executor reads only those | C5 | Reads per agent back to about 6; shorter agent runs |
| S5 | **Models by role.** Planning and judgment (surveyor, interview, planner, conflict resolution) on the strongest model at high reasoning effort; execution (writers, executors, reviewer) on the fast model; mechanics by script (S1) | C2 | Quality where decisions are made, speed and price where work is typed |
| S6 | **One variable per round, 3 reps on the deciding scenario.** No bundled fixes; a rule is adopted only with its own measured delta | C7 | Every change attributable; no regressions slipping in |

## Metrics to track every round
The eight groups of MAINTAINING.md M07 stay. These are the headline efficiency numbers, one line per run:

| KPI | Definition | Target for a one-rule change |
|---|---|---|
| Cost per accepted task | `cost_usd` over hidden tests passed | at most prd-gate |
| Minutes per task | `wall_min` over `tasks_done` | at most prd-gate |
| Main turns per change | `turns` of the main thread | at most 20 |
| Total turns per change | main plus agent turns | at most 70 |
| Main tokens per run | `tokens_main` | at most 3.5M |
| Rework rate | (`rework_commits` + failed gate runs + review fix commits) over `tasks_done` | at most 0.5 |
| Error rate | `tool_errors` over `tool_calls` | at most 2% |
| Ceremony ratio | docs and state tool calls over code and test tool calls | at most 1.0 |
| Quality gates | hidden tests 100%, `contradiction_left` 0, `prd_fidelity` 1.0, `docs_dispatched` true | must hold |

# Evaluation: spec-kit flow versus living truth

Compares the team's current flow (PRD and TRD plus spec-kit) with the living-truth flow on the same synthetic project and the same requests, run unattended with `claude -p`. The candidate is adopted only when it is at least as good on quality and fidelity and not worse on cost (M01 of `MAINTAINING.md`).

## Arms
| Arm | Ref | Spec-kit | Protocol |
|---|---|---|---|
| **SK** (spec-kit flow) | `eval/speckit-baseline` = `main` plus the gate.py fixes found in round 1 | v1.1.0, initialized | `eval/arms/speckit.md` |
| **LT** (living truth) | `feat/living-truth` | none | `eval/arms/living.md` |

The protocol is the one line a team member would give a new colleague about how the team works; it is the only arm-specific text in the prompt (`{protocol}` slot of `eval/prompt.md`). Round 1 showed that without it the agent skips spec-kit even when the constitution requires it, so SK must be told, the way the team tells people.

## Scenarios and repetitions
| ID | Case and size | Exercises | Reps per arm | Budget cap |
|---|---|---|---|---|
| S1 | C5, M | Rule change: non-VIP discount cap 20%, VIP 30% | 2 | US$8 |
| S2 | C5, L | New feature: store credit, new fields, `confirm` | 2 | US$15 |
| S3 | C3, S | Bug: free shipping at exactly 200.00 | 1 | US$8 |
| S4 | C6, S | Refactor: split checkout by responsibility | 1 | US$8 |

12 runs, interleaved by arm, 4 in parallel, timeout 60 minutes each. S1 and S2 are where the flows differ; S3 and S4 check that neither adds overhead to small changes.

## Metrics
Every metric has an ID, a definition, its source and its direction. Sources: **T** the run's `stream-json` transcript, **G** git of the project after the run, **H** hidden tests, **J** the judge (below).

### Quality (hard gates)
| ID | Metric | Definition | Source | Better |
|---|---|---|---|---|
| Q1 | `accept` | Hidden acceptance tests passed over total | H | higher |
| Q2 | `suite_green` | The project's visible suite passes, seed tests included | G | true |
| Q3 | `gate_ok` | The arm's own `gate.py` exits 0 | G | true |
| Q4 | `completed` | The run ended without error, within budget and timeout, with commits after the seed | T, G | true |

### Fidelity
| ID | Metric | Definition | Source | Better |
|---|---|---|---|---|
| F1 | `prd_fidelity` | Facts of the scenario's `prd_facts` stated correctly in the PRD diff, minus contradicted ones, over all facts | J | higher |
| F2 | `plan_coverage` | Plan tasks (from `tasks.md` or `plan.md`) with at least one named file changed by a code commit, over the tasks that name files (a Promote task names none) | G | higher |
| F3 | `plan_drift` | Code files changed that no plan task names, over all code files changed | G | lower |
| F4 | `traceability` | Rule IDs added or changed in the PRD diff that a changed test cites, over those IDs | G | higher |
| F5 | `docs_first` | C5 only: the first commit touching `docs/prd/` comes before the first touching code (feature `CLAUDE.md` maps are docs) | G | true |
| F6 | `promoted` | No PRD row left `planned`, no TRD `## Planned` section left | G | true |
| F7 | `single_source` | Behavior statements added outside `docs/prd/`: `dup_phrases` matches plus `FR-` lines added since the seed plus the files the judge flags | G, J | lower |

### Efficiency
| ID | Metric | Definition | Source | Better |
|---|---|---|---|---|
| E1 | `tokens_total` | Input + output + cache read + cache write, every model, subagents included | T | lower |
| E2 | `cost_usd` | `total_cost_usd` of the result event | T | lower |
| E3 | `wall_min` | Wall-clock minutes of the run | T | lower |
| E4 | `turns` | Main-thread turns | T | lower |
| E5 | `context_peak` | Largest single main-thread request (input + cache read + cache write) | T | lower |
| E6 | `subagents` | Subagents spawned, and their share of E1 | T | report |
| E7 | `min_to_code` | Minutes from start to the first commit touching code | T, G | lower |
| E8 | `doc_bytes` | Bytes added under `docs/`, `specs/`, `changes/` (future reading cost) | G | lower |
| E9 | `cost_per_accept` | E2 over hidden tests passed | T, H | lower |

### Errors and friction
| ID | Metric | Definition | Source | Better |
|---|---|---|---|---|
| R1 | `tool_errors` | Tool results flagged as errors | T | lower |
| R2 | `kit_self_fixes` | Commits touching kit-owned files (`.claude/skills/`, `scripts/`, `.specify/scripts/`): the process broke and the agent patched it | G | lower |
| R3 | `rework_commits` | Commits after the first code commit that re-touch a code file already committed in the run, excluding the promotion task | G | lower |
| R4 | `protocol_adherence` | Required skills invoked over required: SK on C5 needs `prd-gate`, `speckit-specify`, `speckit-plan`, `speckit-tasks`; LT on C5 needs `prd-gate`; both on C3 and C6 need `prd-gate` | T | 1.0 |

## Judge
`eval/judge.py` runs `claude -p --model sonnet` once per run on: `decisions.md`, the `prd_facts` list of `expected.json`, `git diff <seed>..HEAD -- docs/prd`, and the list of other doc files added. It returns JSON: each fact `stated`, `missing` or `contradicted`, and the files outside `docs/prd/` that restate a behavior rule instead of citing its ID. Temperature is not settable, so the judge prompt pins a strict rubric with one example per verdict. About US$0.10 per run.

## Decision rule
Medians per scenario and arm; the **noise band** of a metric is the larger of 10% and the spread (max minus min) observed within either arm for that scenario.

1. **Hard gates.** LT is not adopted when any of these fails: Q1 mean of LT at least that of SK; Q2, Q3 and Q4 true in every LT run; F1 of LT at least SK minus 0.05; R4 of LT equal to 1.0.
2. **Scorecard.** For every other metric and scenario: **win** when LT is better than SK by more than the noise band, **loss** when worse by more than the band, **tie** otherwise.
3. **Adoption.** LT is adopted when the hard gates hold, E1, E2 and E3 are win or tie on both S1 and S2, and in each group (fidelity, efficiency, errors) the losses do not exceed the wins.
4. Otherwise LT is not adopted, and the losing metrics become the work list for the next iteration.

A run that SK fails on R4 is reported, not excluded: if the team's flow skips its own steps unattended, that is a property of the flow.

## Files
| File | Role |
|---|---|
| `fixture/project/`, `fixture/fill.json`, `build.py` | The seed service and its per-arm install (EV01 to EV04 of round 1) |
| `arms.json`, `arms/*.md` | Arm ref, spec-kit flag, protocol, per-scenario caps |
| `scenarios/<id>/` | `request.md`, `decisions.md`, `expected.json` (`case`, `size`, `prd_facts`, `dup_phrases`), `hidden/` |
| `prompt.md` | The one template: `{protocol}`, `{request}`, `{decisions}` |
| `run.py` | Builds, runs `claude -p --output-format stream-json --verbose`, grades, reports. `--dry-run` skips claude and the judge |
| `transcript.py` | `summarize(jsonl) -> dict`: E1 to E7 inputs, R1, R4 skills invoked, result fields |
| `plan_fidelity.py` | Parses `tasks.md` (spec-kit) and `plan.md` (prd-gate) into tasks with files; F2, F3 |
| `grade.py`, `judge.py`, `report.py` | Metrics per run, the judge, the scorecard and the decision |

## Running
```bash
python eval/run.py --dry-run                 # builds every pair, grades the seeds, no spend
python eval/run.py                           # the 12 runs of the table above
```

## Round 1 (2026-10-04), for the record
Arms: `main` plus spec-kit without a protocol versus `feat/living-truth`; one rep, 8 runs, US$27.87. Both arms passed every hidden test. The SK arm never invoked spec-kit, so the round compared the kit without spec-kit against living truth: LT was 5% to 14% cheaper on S1, S3 and S4, and 11% more expensive and 61% slower on S2, where it hit the US$7.50 cap after archiving. Three runs patched two real gate.py bugs (G5 path comparison, HTML header row), which this round fixes in both arms.

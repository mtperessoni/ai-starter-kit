# Efficiency analysis: living truth versus the spec-kit flow

Date: 2026-10-04. Arms: **LT** (living truth, `feat/living-truth`), **SKF** (PRD and TRD plus spec-kit, mandatory), **SKU** (PRD and TRD plus spec-kit, suggested, as the kit described it). Every run unattended with `claude -p`, same prompt, same seed, executor and reviewer subagents requested by the common prompt. Metric definitions: `README.md`, sections Categories, Metrics and Efficiency analysis (X1 to X6).

## Evidence base
| Source | Runs that completed | Notes |
|---|---|---|
| Large suite (12-feature marketplace, 89 rules) | L1 cross-feature rule change: LT 2, SKF 2, SKU 1 plus 1 failure; L2 new feature: 1 per arm | The quota ran out at L2 rep 2; L3 to L8 did not run (`results/2026-10-04-large-v2/`) |
| Pilot | L4 cross-feature bug: LT 1 | Subagents and blind review validated |
| Small suite (one-service fixture) | S1 rule change: 2 per arm; S2 new feature: 1 per arm | Earlier prompt without subagents (`results/2026-10-04-r2/`) |

One to two repetitions per cell: the numbers give direction and size, not statistical significance. The comparable large-suite set is L1 r1, L1 r2 and L2 r1 for each arm.

## X1 Token consumption
| Metric | LT | SKF | SKU |
|---|---|---|---|
| Tokens, sum of the 3 comparable runs | **26.7M** | 36.6M | 42.9M |
| Cost, sum | **US$22.64** | US$30.84 | US$36.13 |
| Main-thread tokens, median | **5.7M** | 10.4M | 12.3M |
| Context peak, median | **165k** | 199k | 192k |
| Share of tokens in subagents | 18 to 38% | 11 to 12% | 0 to 22% |

LT used 27% fewer tokens than SKF and 38% fewer than SKU. The main thread is where it saves: spec-kit's specify, plan and tasks steps run in the main context and stay there for the rest of the session. Small suite, same direction: S1 LT US$2.36 to 2.40, SKU US$2.72 to 3.13, SKF US$4.19 to 4.59; S2 LT US$8.30, SKU US$9.96, SKF US$10.91.

## X2 Efficiency of the subagents
| Metric | LT | SKF | SKU |
|---|---|---|---|
| Subagents spawned (3 runs) | 10 | 11 | 8, all in L2; **none in L1** |
| Wasted subagents (no change, no review) | 0 | 0 | 0 |
| Errors inside subagents | 5 (all in L2) | 3 | 9 |
| Plan tasks per executor | 2.0, 1.5 | 1.5, **0.25**, 7.0 | 3.5 |
| Plan coverage / plan drift | **1.0 / 0.0** in all 3 | 1.0/0.67, 0.17/0.5, 1.0/0.17 | 0.88/0.0 |

LT's executors delivered exactly the planned tasks and nothing outside them. SKF had two plans (spec-kit's `tasks.md` and prd-gate's plan), and executors followed one while code drifted from the other: up to 67% of changed code files were named by no task, and in one run 4 executors covered one task in six. SKU ignored the request for subagents in both L1 runs.

## X3 Error rate during implementation
| Metric | LT | SKF | SKU |
|---|---|---|---|
| Tool errors / tool calls | 13 / 447 = 2.9% | 11 / 457 = **2.4%** | 24 / 496 = 4.8% |
| Test runs that failed / test runs | 11 / 39 | 5 / 44 | 4 / 26 |
| Patches to the kit itself | 0 | 0 | 0 |
| Runs that failed to finish | **0 of 3** | 0 of 3 | **1 of 3** (budget cap after 110 turns) |

Failed test runs include the red step of test first, so a higher count with more test runs is mostly discipline, not breakage: LT ran 39 test runs with 11 red, the expected pattern of writing the failing test first. SKF had the lowest tool error rate; SKU the highest and the only run that never finished. The gate fixes of this branch removed kit self-patching (3 of 8 runs had patched the gate before them).

## X4 Time to complete
| Metric | LT | SKF | SKU |
|---|---|---|---|
| Wall time, sum of 3 runs | **52.3 min** | 58.9 min | 68.4 min |
| Minutes to the first code commit, median | **11.3** | 11.6 | 16.1 |
| L2 new feature | **18.5 min** | 21.0 min | 33.6 min |

LT was 11% faster than SKF and 23% faster than SKU. The gap grows with size: on the new feature, SKU took 1.8 times as long.

## X5 Reviews needed for good code
| Metric | LT | SKF | SKU |
|---|---|---|---|
| Review rounds per run | 2, 2, 2 | 1, 1, 3 | 0, 0, 2 |
| Fix commits after the first review | 3, 3, 3 | 0, 1, 4 | 0, 0, **9** |
| Findings left for a blind reviewer afterwards | 1, 0, 3 | 1, 1, 2 | 0, 1, 3 |

LT ran the review loop every time and converged in 2 rounds with 3 fixes. SKF was uneven. SKU skipped review in two of three runs and, when it did review the new feature, needed 9 fix commits. The findings left at the end are similar across arms and all medium or low.

## X6 Code with the fewest problems
| Metric | LT | SKF | SKU |
|---|---|---|---|
| Hidden acceptance tests | 100% in every run | 100% | 100% in the runs that finished |
| Visible suite and gate | green | green | green |
| Blind review: critical and high findings | **0** | **0** | **0** |
| Blind review: medium plus low | 4 | 4 | 4 |
| Blind reviewer would approve | all | all | all |

Code quality is a tie: no arm produced a bug the hidden tests or the blind reviewer found. What differs is cost and process, not the code that ships.

## Source-of-truth fidelity
| Metric | LT | SKF | SKU |
|---|---|---|---|
| PRD facts stated (judge) | 1.0, 1.0, 0.86 | 1.0, 1.0, 1.0 | 1.0, 1.0 |
| Behavior restated outside the PRD (matches) | 11, 9, 1 | 32, 43, 31 | 1, 31, 22 |
| Doc bytes added | 7 to 13 KB | 26 to 34 KB | 1 to 35 KB |

The one PRD fact LT missed on L2 is the data model, which LT's own rule (LT03) sends to `design.md`, the TRD and the code instead of the PRD; the judge counts the PRD only. SKF restated rule text three to four times more than LT, which is the duplication this change set out to remove. LT still restates some rule text, through the literal contract each plan task copies.

## Verdict
**Living truth is the more efficient flow, with the same code quality.** Over the comparable runs it used 27% fewer tokens and 27% less cost than spec-kit used as mandatory, and 38% and 37% less than spec-kit as suggested; it was 11% and 23% faster; it followed its plan completely; it ran the review loop every time; and it wrote about a third of the documentation with a fifth of the duplicated rule text (21 restatements against 106 for SKF). Code quality was the same in every arm: 100% of the hidden tests and no critical or high finding.

Where LT is not ahead: SKF had a slightly lower tool error rate (2.4% versus 2.9%), and LT made more fix commits after review (consistent, 3 per run) than SKF on the rule change.

## Work list for LT
- Plan tasks copy the rule row literally (WF19 contract); cite the ID and link the row instead, to bring the restatements of L1 (9 to 11) toward zero.
- Subagent errors concentrated on the new feature (5 in L2): look at what the executor of a new feature module lacks in its context pack.
- The judge should read `design.md` and the TRD for data-model facts, so LT is not penalized for putting them where its rules say.

## Remaining runs
40 large-suite pairs did not run (quota). To complete the round and firm up these numbers:
```bash
python eval/run.py --config eval/arms-large.json --out eval/results/2026-10-04-large-v2 --only <pairs with status skipped_rate_limit or rate_limited>
python eval/regrade.py eval/results/2026-10-04-large-v2 --config eval/arms-large.json
```

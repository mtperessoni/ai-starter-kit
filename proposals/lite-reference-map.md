# prd-flow lite: where every instruction went

Companion of [`plan-prd-flow-lite.md`](plan-prd-flow-lite.md) (decision L18). Old paths are under `kit/.claude/skills/prd-flow/` unless they start with `agents/` (`kit/.claude/agents/prd-flow-*.md`). The nine references became five; the old files `classification.md`, `impact.md`, `interview.md`, `prd-writing.md`, `trd-planned.md`, `agent-plan.md`, `execution.md` and `review.md` are deleted.

## 1. Old file and heading to new file and heading
| Old | New |
|---|---|
| SKILL.md "Chief card" | SKILL.md "Chief card" (adds cleanup SA56, watch SA57, surveyor model per mode L2) |
| SKILL.md "Cases", "C5 route", "Returns", "State", "Rules" | SKILL.md same headings; the review policy line moved to SKILL.md "Review"; warm fix and recheck (L7) in the failure table |
| dispatch.md "Prompt template" | dispatch.md "Prompt" (adds `Model`, `Background`, the warm recheck line, docs `short` and `plan`; drops the `general-purpose` fallback, L12) |
| dispatch.md "Rules" DP01 to DP09 | dispatch.md "Rules" |
| dispatch.md "Behavior by role" BR01 to BR07 | retired, see section 2 |
| dispatch.md "Cross-repo mode" DP10 to DP13 | dispatch.md "Cross-repo" (L17 in DP10 and DP13) |
| classification.md "Cases", "Size", "A new context is a new PRD", "Classification traps", "Behavior of a real session" | survey.md "Cases" |
| classification.md "PRD versus code divergence" | survey.md "Divergence" |
| impact.md "Functional proof" | survey.md "Sweep" (F3) and "Proof" (verdicts); F1, F2 printed by `prd-sweep` |
| impact.md "Sweep", "Sweep by size" | survey.md "Sweep" (step 1 the script, step 2 the judgment, scope table) |
| impact.md "Conflicts" | survey.md "Conflicts" |
| impact.md "The sheet" (mechanism, blind spots, rollback), "Survey section" trade-offs line | sheet.md "Sheet rules" (Mechanism, Blind spots) |
| impact.md "Survey section", "Format of `pack.md`", "Protected rules" | survey.md "Survey section", "Pack", "Protected rules" |
| interview.md header table | sheet.md intro; SKILL.md "C5 route" |
| interview.md "Format of `sheet.md`", "Sheet rules" | sheet.md "Format", "Sheet rules" |
| interview.md "Answers" | sheet.md "Answers" ("Not understood" moved to SKILL.md "Chief card" Explain) |
| interview.md "Records" `decisions.md` | sheet.md "decisions.md" (with `Reply` lines, L3) |
| interview.md "Records" `answers.md`, `rules.md`, `approved-rules.md`, render | retired (L3, L4) |
| interview.md "Sheet lint" | sheet.md "Lint" (Q3 in its new form, L4) |
| prd-writing.md "Who writes what", "Writer steps" | write.md "Apply" |
| prd-writing.md "Contract and transition lines", "Where to write", "Rule rows" | write.md "Rule rows" |
| prd-writing.md "CHANGELOG", "INDEX and README" | write.md "CHANGELOG" (format of the plan's "Formats") |
| prd-writing.md "Promotion", "HTML" | write.md "Promotion" |
| prd-writing.md "Gate and commit" | write.md "Gate" and "Apply" step 6 (one commit, L6) |
| trd-planned.md "Planned" section, TP01 to TP07, "Size and split", "Area without a file", "Invariants and tests", "Merge of Planned" | write.md "TRD" (Planned only for size L, L5) |
| trd-planned.md "Gate and commit" | write.md "Gate", "Apply" step 6 |
| agent-plan.md "Where the plan lives" | write.md "Change folder" |
| agent-plan.md plan commit, waves, `## Plan` | write.md "Plan" |
| agent-plan.md "Docs fan-out by context" | write.md "Apply" (Fan-out) |
| agent-plan.md "Plan header", "Routing by Change via" | write.md "Plan" |
| agent-plan.md "Format of a task" and its rules | write.md "Card" (adds `Why:`, L9) |
| agent-plan.md Deliveries paragraph | run.md "Deliveries" |
| agent-plan.md "Fix card" | write.md "Fix card" |
| agent-plan.md "Execution is not in the plan", "Promote is not a task", "Presentation" | write.md "Plan", "Promotion", "Apply" step 7 |
| execution.md "Where to execute" | SKILL.md "State" (E01), dispatch.md DP03 (E02) |
| execution.md "Wave loop" | dispatch.md DP02, DP03, DP06, DP12; run.md "Task", "Every agent" "Commit"; SKILL.md "Chief card" |
| execution.md "Rule change in the middle of execution" | run.md "Short C5 in the middle of execution" |
| execution.md "Cost per agent" | run.md "Every agent", "Task", V08, V09; dispatch.md DP07; SKILL.md "Review" (brake) |
| execution.md "Closing" | run.md "Close", "Deliveries" |
| review.md "Review table", "Routing by return" | run.md "Review"; SKILL.md "Returns"; reviewer and recheck "Failure routes" |
| review.md "Rules" V01 to V10 | run.md "Review" |
| review.md "Record in `## Chief`" | dispatch.md "Records in `## Chief`" |
| agents/* "Common rules" | run.md "Every agent" (each agent links it) |
| agents/* frontmatter `hooks:` | removed: `settings.json` runs the guard for every subagent (L12) |
| agents/surveyor "Batch 1", "Preflight", "Modes", "Failure routes", "Return" | agents/surveyor "Batch 1", "Modes", "Failure routes", "Return" |
| agents/docs "Modes", "PRD", "TRD", "Plan" | write.md "Apply" and its modes table; agents/docs "Steps" |
| agents/executor "task", "fix", "close" | run.md "Task", "Deliveries", "Fix", "Close"; agents/executor "Failure routes" |
| agents/reviewer "Inputs", "How" | run.md "Review"; agents/reviewer gains the warm `recheck` mode (L7) |
| agents/recheck | unchanged role, now the cold fallback (L7) |
| repo.md every section and Gate config key | repo.md, same sections and keys; key explanations one line each in one table; "Commands" by role |

## 2. Every rule ID of the old instruction files
| IDs | Status | Where now, or the decision that retires it |
|---|---|---|
| C0 to C6 | kept | SKILL.md "Cases" (route), survey.md "Cases" (signals, traps) |
| R01, R03, R07, R09 | kept | SKILL.md "Rules" |
| DP01 to DP09 | kept | dispatch.md "Rules"; DP02 absorbs E04 (width, rate limits, rerun alone), DP03 absorbs E02 and E07, DP07 absorbs E18 and E23, DP08 now errors only plus a warnings line (L8) |
| DP10 to DP13 | kept | dispatch.md "Cross-repo"; DP10 and DP13 carry L17; DP12 absorbs E22 |
| BR01 | retired (L18, a restatement) | SKILL.md "Chief card", DP01, DP03 |
| BR02 | retired (L18) | agents/surveyor "Batch 1" (glossary, intros, journey first); sheet.md "Sheet rules" |
| BR03 | retired (L18) | write.md "Apply" steps 5 and 6 |
| BR04 | retired (L18, pointed at the agent file) | agents/executor |
| BR05, BR07 | retired (L18) | DP07 |
| BR06 | retired (L18) | run.md "Review" |
| E01 | kept | SKILL.md "State" |
| E02 | kept | DP03 |
| E03 | kept | DP06 |
| E04 | kept | DP02; the wave table from the gate, write.md "Plan" |
| E05 | kept | run.md "Every agent" "Commit"; agents/executor "Failure routes" |
| E06 | kept | run.md "Review" table; write.md "Plan" (`Review:` line) |
| E07 | kept | DP03, DP04; run.md "Task" (`Interrupted:`) |
| E08 to E10 | kept, amended (L3, L4: no `rules.md`, `delta.md` or render) | run.md "Short C5 in the middle of execution" |
| E11 | kept | run.md V09 |
| E12 | kept | run.md "Every agent" "Subagents" |
| E13 | kept | write.md "Card" (`Model:`) |
| E14 | kept | run.md V08 |
| E15 | kept | dispatch.md "Prompt" |
| E16 | kept | run.md "Every agent" "Commands" |
| E17 | kept | SKILL.md "Review" (brake) |
| E18 | kept | DP07 (chief), run.md "Task" step 2 (executor), V09 |
| E19 | kept | run.md "Task" step 3 |
| E20 | kept | run.md "Close" |
| E21 | kept | run.md "Deliveries" |
| E22 | kept | DP12 |
| E23 | kept | SKILL.md "Chief card", DP07 |
| V01, V03, V04, V06, V09, V10 | kept | run.md "Review" |
| V02, V05, V07 | kept | run.md "Review" (ID), the chief's action in SKILL.md "Review" |
| V08 | kept, values per L10 | run.md "Review" V08, the single home of ceilings |
| K01, K02, K05, K06 local, K11 candidates, K12, K14 candidates | kept, collected by `prd_sweep.py` (L1) | survey.md "Sweep" step 1 |
| K03, K04, K06 remote, K07, K08, K09, K10, K11 reading, K13, K14 verdicts | kept | survey.md "Sweep" step 2 |
| F1, F2 | kept, by `prd_sweep.py` (L1) | survey.md "Sweep", "Proof" |
| F3 | kept | survey.md "Sweep" step 2 |
| TP01 to TP07 | kept; Planned only for size L (L5) | write.md "TRD" |
| P1, P2, P3 (promotion steps) | kept | write.md "Promotion" |
| P11, P13 to P16 | retired (L8) | `plan_strict` now names only P17 in repo.md |
| P17 | kept (script code) | repo.md `plan_strict`, `shared_files` |
| S1 to S6 | kept | sheet.md "Lint"; S4 also repo.md `plain_words` |
| Q3 | kept, new form (L4) | sheet.md "Lint", write.md "Gate" |
| Q5 | kept, new form (L4) | write.md "Gate" |
| Q2, Q4 (named by the gate) | Q2 kept in its new form (write.md "Gate"); Q4 retired (L8: it compared `approved-rules.md`) | |
| G2 (close order), G19, G21 | kept (script codes) | run.md "Close"; agents/executor "Failure routes" |
| G3, G5, G8, G20, G26, G28, G29, G30, G31, G32 | kept (script codes) | repo.md Gate config table; write.md "Rule rows", "Promotion", "TRD" |
| G25, G27 | kept (script codes) | write.md "TRD" (TP05), "Gate" |
| LT01, LT07, LT11 | kept | repo.md "Layout" |
| CS-NNN | kept (finding ID format) | run.md "Review" |

## 3. Behavior fixes of the one-pass branch, kept
| Fix | Where |
|---|---|
| Explain a sheet item with today's rule and an example | SKILL.md "Chief card" Explain |
| The executor lints its own files (`fix-files`, `lint-files`) | run.md "Task" step 2; repo.md "Commands" |
| Commit from a message file (`-F <file>`, never `-F -`) | run.md "Every agent" "Commit" |
| One interpreter (`Python:` from `gates.sh python`) | dispatch.md "Prompt"; run.md "Every agent" "Interpreter" |
| Reap on a background-work notice | SKILL.md "Chief card" Orphans |
| Cleanup never in the same message as a suite start | SKILL.md "Chief card" Cleanup |

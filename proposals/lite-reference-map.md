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

## Ported from main
Merge of `origin/main` (one-pass interview fixes, base `a979cd6`) into the lite structure. One line per ported change, then the lite decisions that won.

| Change on main (old home) | Lite home |
|---|---|
| One follow-up, hard stop: no sheet after `Answers 2`, what stays open is a `Q-` row with the default (interview.md "Answers", agents/docs `apply`) | sheet.md "Answers"; write.md "Apply" step 1; SKILL.md "C5 route" step 3 |
| TRD-only decision: the one `sheet-2.md` while unused, else a `Q-` row, never a second sheet (trd-planned.md TP06, agents/docs Plan step 4) | write.md TP06; agents/docs "Failure routes" |
| Gate red meaning an unclear rule: fix once, then a `Q-` row, never `sheet-2.md` for a gate (agents/docs) | agents/docs "Failure routes" |
| Unclear answer routes to `sheet-2.md` only before `Answers 2` (agents/docs) | agents/docs "Failure routes" |
| Approval by chat reply, no AskUserQuestion: docs returns `Route: none` and `Next:` print and wait (SKILL.md step 5, agents/docs Return) | SKILL.md "C5 route" step 4; write.md "Apply" step 7; agents/docs "Return" |
| Short sheets in their own file `sheet-short-<k>.md`, never over `sheet.md`; linted with the others (interview.md "Short sheet", agents/surveyor `short`) | sheet.md intro and "Lint"; agents/surveyor `short` and "Return"; run.md "Short C5" step 2; SKILL.md "Chief card" Tools |
| A short C5 ends at its sheet reply, which is its approval (SKILL.md "Returns", execution.md E09) | SKILL.md "Returns"; run.md "Short C5" step 3; sheet.md "Answers"; write.md modes `short` |
| Sheet limits and shape checks live only in "Lint"; the duplicated Context, One topic and Numbers rows and the "at most 8" counts leave "Sheet rules" (interview.md) | sheet.md "Sheet rules" intro and "Lint" |
| C4 close needs no baseline and no compare; `close <slug> --case <C>` (dispatch.md DP06, execution.md E20, agents/executor close) | dispatch.md DP06 and executor task line; run.md "Close" step 3; repo.md "Commands"; kit/AGENTS.md |
| Baseline taken at close would hide the change's own failures (DP06, agents/executor) | dispatch.md DP06; agents/executor "Failure routes" |
| Wave end: reap as its own call, verify and reviewer in the next message (DP07) | dispatch.md DP07; SKILL.md "Chief card" Wave |
| The reviewer and recheck never read the wave verify, which runs beside them (DP07, review.md V09, agents/reviewer, agents/recheck) | dispatch.md DP07; run.md "Review" and V09; agents/reviewer; agents/recheck |
| Restart `compare` after the last fix; close on "compare is still running" waits, on "no compare result" starts it (DP07, E20) | dispatch.md DP07; run.md "Close" step 3 and V09; agents/executor "Failure routes" |
| Recheck all resolved: `Next:` "the wave is closed: next wave or executor close" (agents/recheck) | agents/recheck and agents/reviewer "Failure routes" |
| Commit message files `msg-<task>.txt`, `msg-fix-<n>.txt`, `msg-close.txt` (agents/executor) | agents/executor intro; run.md "Every agent" Commit |
| `fix-files <file>...`, `lint-files <file>...`, `verify`, `python`, `close --case`, `settings-check` listed (kit/AGENTS.md) | kit/AGENTS.md (main's lines kept); repo.md "Commands" |
| `settings-check` for the access check of the files the flow writes | agents/surveyor batch 1 (`full`); repo.md "Commands" Surveyor |
| `move <source> <start> <end> <destination> [--at LINE]` signature (execution.md E19, repo.md, agents/executor) | run.md "Task" step 3; repo.md "Commands" |
| `next_change_number.py` with the prompt's `Python:` interpreter (agents/surveyor Preflight) | agents/surveyor batch 1 (`full`) |
| Unclear repository: the surveyor returns `Route: user: <which repository>` before any survey (SKILL.md step 0, agents/surveyor) | agents/surveyor batch 1; SKILL.md "C5 route" step 0 |
| A second slug in one tree: tell the user to use its own worktree and stop (SKILL.md step 0) | SKILL.md "C5 route" step 0 |
| `Python:` run once by the chief (dispatch.md "Prompt template") | dispatch.md "Prompt" |
| Fresh session only past about 120k tokens; the "more than 2 waves left" trigger and the fast-model offer leave (E01, E02) | SKILL.md "State"; dispatch.md DP03 |
| R09: "several rules" alone sends a full C5 (no "new dimension") | SKILL.md "Rules" |
| Fold wording "moved into <files>", never the removed word (prd-writing.md P3) | write.md P3 |
| Stale HTML is printed only under `gate.py --html` (G29, G32) (prd-writing.md "HTML", repo.md) | write.md "Promotion"; repo.md key table |
| G25 is gone: TP05 no longer cites it (trd-planned.md TP05) | write.md TP05 |
| "interview" becomes "decision sheet" in descriptions (SKILL.md, classification.md, prd-writing.md, repo.md) | SKILL.md description; lite files already said "sheet" |
| Guard hook unescapes backslashes in the configured interpreter (`sed 's/\\\\/\\/g'`, agents frontmatter) | not ported here: lite moved the guard to `kit/.claude/settings.json` (L12), owned by another agent; that file must carry the fix |

Lite decisions that won over main:

| Main | Lite, kept |
|---|---|
| Docs returns the rule diff and wave table inline in the return | `<state>/diff.md`, printed verbatim by the chief (write.md "Apply" step 7); only the approval by chat reply was ported |
| Docs `apply` writes `answers.md`, `rules.md`, renders with `state_record.py`; promote fails without `approved-rules.md` | L3, L4: the PRD diff and the CHANGELOG entry are the approved set; no such route in agents/executor |
| Several docs commits (rules, prose, TRD, changes) | L6: one `docs(prd): <sentence>` commit |
| Short C5 through docs `apply` with `Case short` and items `s<k>.<n>` in `answers.md` | docs `short <YYYY-MM-DD>` with the reply verbatim (`answers.md` retired) |
| C2 over one task routes to docs `short` | `Route: docs plan` (docs `plan` mode) |
| promote "PRD file not found" routes to docs `fold` | docs `adjust` (the entry or rows are wrong, nothing to fold) |
| `general-purpose` fallback agent; `hooks:` frontmatter in each agent | L12: `prd-flow-<role>` only; the guard runs from `settings.json` |
| Verify failures mapped by the chief alone | Kept main's "reviewer never reads verify", and lite's warm fix: finding lines by `Task:` to warm executors, verify failures with the `Task: none` lines to one executor `fix` |
| CHANGELOG entry heading `## <slug> (...)` | `## <Name of the change> (...)`, the plan's "Formats" (write.md "CHANGELOG") |
| Agents' own "Common rules" tables and ceilings | run.md "Every agent" and V08, the one home |

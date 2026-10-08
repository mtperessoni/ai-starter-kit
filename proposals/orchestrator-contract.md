# Orchestrator contract for prd-flow

Date: 2026-10-08. Branch `fix/prd-flow-cost`. Sources: `kit/.claude/skills/prd-flow/SKILL.md` (SK), the five `kit/.claude/agents/prd-flow-*.md` (surveyor SV, docs DO, executor EX, reviewer RV, recheck RC), `reference/*.md` (execution EXE, review REV, interview INT, impact IMP, agent-plan AP, classification CL), `promote.py`, `gate*.py`, `kit/scripts/close_gate.py`, `eval/protocol.py`, and the evidence in `eval/AUDIT-v5.md`, `eval/AUDIT-prd-flow.md`, `proposals/efficiency-audit.md`, `rules/09-lessons.md` LS24 to LS28. `file:N` is a line number.

Goal: the main thread only orchestrates; subagents and scripts do the work; every handoff artifact is complete for its consumer.

**Verdict: not guaranteed today.** The C5 happy path has an owner for every step, and the closing ceremony is one script. But (a) the light route (C1 to C4, C6) and step 4 are inline work by design, (b) about ten failure paths have no owner and SK:16 tells the main to "resolve the gap first", (c) returns are free text the main must interpret, (d) resume tells the main to read agents' files that the card forbids, and (e) almost every rule is enforced only by prose; the only mechanical checks are artifact gates and an eval metric that misses whole categories.

Main may: **dispatch** (an agent or a script), **commit** (one Bash from returned fields), **ask** (the user, with text an agent prepared), **record** (copy a returned field into `state.md`), **nothing**. Flags: **U** owner unclear, **M** defaults to the main, **G** the main resolves a gap by doing work. "Proposed" is the owner this contract assigns.

## 1. Responsibility matrix

| # | Action | Owner today | Inputs | Output | Main may | Flag, proposed owner |
|---|---|---|---|---|---|---|
| 1 | Classify a clear request, state case and size | main | request, one INDEX Grep | case line | decide | ok |
| 2 | Classify an unclear request | surveyor | request | case, size in confrontation line 1 | dispatch | ok (SV:10) |
| 3 | C0 hand-over | `/prd-create`, `/trd-create` | none | PRD, TRD | dispatch | ok |
| 4 | C1 answer: Grep INDEX, read rows, map, TRD, verify Source has a caller | main | INDEX, PRD, TRD, source | answer with IDs, "verified" | nothing | **M** (SK:22,32; CL:9). Proposed: surveyor `light` |
| 5 | C2 to C4, C6 check: Source exists, matches, caller outside tests | main | PRD rows, source | divergence block | ask | **M** (SK:32). Proposed: surveyor `light` returns the block |
| 6 | Show divergence, ask C3 / C4 / C5 | main | divergence block | user choice | ask | ok |
| 7 | Decide "over one task" in C2 (docs `plan` or not) | main | rows, code | yes/no | decide | **U M** (SK:23). Proposed: surveyor `light` returns `Tasks: 1|n` |
| 8 | Task card for C3, C6, one-task C2 (Contract, Owns, Read, Tests, Leave) | nobody | rows, TRD, code | card in prompt | nothing | **U M** (EX:10 "Plan: none" plus card). Proposed: surveyor `light` writes `card.md` |
| 9 | Minimal `state.md` (C2, C3, C6) and C4 divergence lines | main | light-route result | state.md | record | ok once 5 returns the fields; format undefined (**U**) |
| 10 | C5 step 1: slug, `gates.sh context`, approver | main | request | prompt | dispatch, run | ok |
| 11 | Step 2: state folder, pack, impact, scaffolds, `decisions.md`, gate `--pack` | surveyor | request, PRD, TRD, code | files, confrontation | dispatch | ok |
| 12 | Step 3: show confrontation, ask change / keep / adjust | main | surveyor return | choice | ask | ok |
| 13 | Step 3 "adjust (back to 2)": prompt of the new surveyor | main | user words | prompt | dispatch | **U** what the prompt carries. Proposed: `request:` plus `adjust:` line |
| 14 | Protected rule still holds? record `Protected: <ID> · <route>` | main | return `Protected:` | state line | ask, record | ok |
| 15 | Rule owner agreed; record owner | main | return `Owner` | DEC row | ask, record | **M** writes a DEC row. Proposed: answer to scribe (row 17) |
| 16 | Step 4: ask open dimensions (at most 4 per round) | main | `interview.md` open rows | answers | ask | ok, but questions sit in a file, not the return |
| 17 | Step 4: write rule text, Example, conflict Resolution, Supersedes, DEC rows | main | answers, scaffolds | approved-rules, decisions | nothing | **M** (INT:5, SK:40). LS25: free-form rows looped the writer. Proposed: docs `rules` (scribe) |
| 18 | Step 4: `gate.py --rules`, fix own files, at most 2 reruns | main | approved-rules, interview | gate line | run | **M G** (fixing format is work). Proposed: scribe |
| 19 | Step 4: read-back, "it is clear", `Confirmed:` line | main | rows | Confirmed line | ask, record | ok (rows come from scribe return) |
| 20 | Step 5: PRD, ADR, CHANGELOG, INDEX, HTML, `--applied`, commit `docs(prd)` | docs | approved-rules, interview, pack, decisions | commit, `writing.md` | dispatch | ok; note docs commits, executor does not (two commit owners) |
| 21 | Step 5 fan-out: docs `C5 context` per context, then docs `plan` merges | docs | as 20 | files, one commit | dispatch | ok |
| 22 | Step 6: docs stopped; show gate line and non-table changes | main | docs return | confirmation | ask | **U** (SK:42): a red gate is shown as a user question. Proposed: red gate = docs rerun (row 52); only non-table changes are asked |
| 23 | Steps 7, 8: TRD Planned, brief, design, plan, gate `--step plan`, commit, wave table and `Execution:` line in state.md | docs | pack, writing, PRD rows | plan, state lines | dispatch | ok |
| 24 | Step 9: approve plan from returned table | main | docs return | approval | ask | ok |
| 25 | Step 9: user wants the plan adjusted | main | user words | edited plan | nothing | **U M** (AP:87 "Adjust until approved"; `changes/` missing from SK:13 never-list). Proposed: docs `plan` re-dispatch |
| 26 | Baseline before wave 1 | main | slug | baseline file | run | ok |
| 27 | Record wave base `git rev-parse HEAD`; base before a fix | main | none | range | run, record | **U** for the fix base (RC needs `<base>..<head>`) |
| 28 | Build executor prompts: Grep `^### T`, read cards by range | main | plan | prompts | dispatch | ok, costs 1 + n calls. Proposed: script prints prompts |
| 29 | Implement task test first; deliveries block | executor | card, rows, DEC rows, deliveries of deps | files, block, message | dispatch | ok |
| 30 | Commit each return (one Bash), due state lines | main | `Files`, `Commit` | commit | commit | ok |
| 31 | File list does not match the stat | executor (new) | stat | fixed list | dispatch | **U**: `git diff --stat` ignores untracked and unlisted files (EXE:17), so the check cannot fire. Proposed: commit script |
| 32 | Build reviewer prompt: rules, DEC, Leave, Lens of all wave cards | main | wave cards | prompt | dispatch | ok, assembly by hand. Proposed: script |
| 33 | Wave review | reviewer | wave diff, rows | findings | dispatch | ok |
| 34 | Decide per finding: Critical fix; High fix "if it fits the approved rules", else ask; Medium, Low pending | main | findings | decision | decide | **G** (SK:47, REV V04): judging "fits" needs rules and diff; FLOW-S8 read the diff to check. Proposed: reviewer emits `Act:` |
| 35 | Fix findings | executor (fix mode) | finding lines | files, message | dispatch | **U**: no Owns or Read for a fixer (EX:10, REV V10) |
| 36 | Scoped recheck after a Critical or High fix | recheck | fix diff, finding IDs | resolved/open | dispatch | ok |
| 37 | Review row, `review: N/5`, pending, cost line in state.md | main | returns | state lines | record | ok |
| 38 | Cascade or round 5 with open Critical: stop and ask | main | counts | user choice | ask | ok |
| 39 | Pick the next wave | main | state.md | dispatch | dispatch | **U**: no `Done:` field; wave status inferred |
| 40 | Gap in a return: classify rule divergence vs technical detail | main | free-text `Gaps:` | route | decide | **G** (EXE:17). Proposed: agent sets `route` |
| 41 | Gap is a technical detail: "a question or a new task" | main | gap | question or card | ask, nothing | **M** writes the new card. Proposed: docs `card` |
| 42 | Short C5: stop tasks touching the behavior | main | running agents | stopped tasks | nothing | **U** (EXE:26): no mechanism; partial work patch by main (EXE:19) |
| 43 | Short C5: surveyor short, dated scaffolds | surveyor | touched rules | confrontation | dispatch | ok |
| 44 | Short C5: dated table, Confirmed, DEC rows, row edits, `--rules` | main | answers | files | ask | **M** (EXE:27-28). Proposed: scribe |
| 45 | Short C5: PRD, TRD, append tasks | docs `short` | dated section | commits, tasks | dispatch | **U**: wave table refresh and rewrite of the stopped card unassigned |
| 46 | Resume: read `state.md` | main | state.md | phase | record | ok |
| 47 | Resume: read the phase file (`impact.md`, `writing.md`, `deliveries.md`) | main | agents' files | context | nothing | **M**: SK:52 contradicts SK:13 ("never impact.md", "agents' files"). Proposed: `Next:` line |
| 48 | Resume: pack freshness `git diff --quiet`; missing wave table: `--step plan` | main | pack Base | new surveyor or table | run | ok |
| 49 | `promote.py <slug>` | script | approved-rules, deliveries, decisions | PRD, CHANGELOG, HTML, archive | run | ok |
| 50 | Promote ERROR: rule without `Source:` | executor (promote mode) | error lines | deliveries lines | dispatch | ok (SK:14) |
| 51 | Promote ERROR: superseded ID matches no row | nobody | approved-rules (main's file) | fix | nothing | **U M** (promote.py:315). Proposed: scribe |
| 52 | Gate red after 2 reruns inside any agent ("resolved first") | nobody | ERROR lines | fix | nothing | **U G** (SK:16, DO:19). AUDIT-prd-flow: main ran `gate.py` 33 times, read gate source 4. Proposed: new agent of the same role with the lines; third time ask |
| 53 | Promote ERROR: HTML rebuild, `git mv` archive, `gate --final` exit 1 | nobody | error line | fix | nothing | **U** (promote.py:293,339,355). Proposed: owner printed by promote |
| 54 | Promote WARN: fold, `design.md` destinations | docs `fold` | warning lines | files | dispatch | ok; who commits `fold` files is **U** (DO:32 "no commit") |
| 55 | Commit the promote result | main | promote output | commit | commit | **U**: promote prints no file list or message, so the main needs `git status` (forbidden) or `add -A` |
| 56 | `gates.sh close <slug>` | script | baseline, tree | block | run | ok |
| 57 | Close FAILED compare or lint | executor | failure lines | fix | dispatch | ok |
| 58 | Close FAILED trailers | nobody | range | rewritten messages | nothing | **U**: needs a history rewrite; executor never commits |
| 59 | Close FAILED `gate --final` (G19, G20, G21) | executor | failure lines | fix | dispatch | **U**: G19, G21 are docs or other changes' (gate_plan.py:133-150) |
| 60 | Close FAILED "baseline missing" | main | none | baseline | run | **U**: a baseline taken now includes the change's own failures |
| 61 | Agent at ceiling: replacement with handoff of at most 10 lines | main | free-text "what is left" | prompt | dispatch | **U M**: the main writes the handoff (EXE:37); partial files committed or not is unstated |
| 62 | Brake (E17): two ceilings, or a wave 2x slower | main | durations | report | ask | ok, durations not in returns |
| 63 | Final report | main | close block, state.md | summary | record | ok |
| 64 | Sibling or shared PRD change, consumer handoff note | nobody | K08, K13 lines | note | ask | **U** (IMP:15,20; AP:39) |

## 2. Artifact contracts

| Artifact | Writer | Readers | Format home | Budget | Mechanical check at handoff | Lifetime | Defect |
|---|---|---|---|---|---|---|---|
| `state.md` | surveyor (scaffold), main (phase, review, pending, cost, Protected, gate line), docs (plan path, wave table, `Execution:`) | main, resume, docs (`--rules` line, ADR) | scattered: SV:30, SK:12, DO:21, EXE:8, REV:28 | none | **none** | until close | 3 writers; no phase enum; no `Done:` or `Next:`; "ADR path" (DO:26) vs `Protected: X · ADR` (IMP:93) can be misread |
| `pack.md` | surveyor | docs, executor, reviewer | SV:38-76 | none | `gate.py --pack` (sections, literal rows) | until close | short C5 appends; no size budget |
| `impact.md` | surveyor | eval, resume (main) | IMP:54-80 | 25 lines (15 short) | **none** | until close | duplicated in the return; resume rereads it |
| `interview.md` | surveyor, main | docs (D08, D13), `--rules` Q3 | INT:42-64 | none | `gate.py --rules` Q3 | until close | open questions live only here, not in the return |
| `approved-rules.md` | surveyor, main | docs, executor, reviewer, promote | INT:66-92 | none | `--rules` Q2 to Q5; `--applied` Q4 | until close | main writes gate formats by hand (LS25) |
| `decisions.md` | surveyor (template), main (DEC rows) | docs, executor, reviewer by ID, promote | INT:94 | none | **none** | committed, archived | DEC IDs cited on cards are never checked to exist |
| `writing.md` | docs | docs (`trd+plan`), resume | DO:42,47 | none | **none** | until close | read by the main on resume against SK:13 |
| `brief.md`, `design.md` | docs | executor via Read, promote fold | templates | none | `gate.py --change` | archived | ok |
| Plan task cards | docs | main (range), executor, reviewer (via main) | AP:44-58 | 25 lines a card, `plan_budget_kb` | `--step plan`: Owns (error), Lens, Model (warn), IDs exist, Owns overlap per wave (P7) | archived | not checked: Contract, Read, Tests, Decisions, Leave, Commit, Depends on, card length; `Reviewer:` alias still accepted (gate_plan.py:28) |
| Wave table and `Execution:` line | docs (copied from gate) | main | DO:57-58 | about 10 lines | **none** (verbatim copy unchecked) | until close | not refreshed after a short C5 |
| `deliveries.md` | executors (append) | dependent executors, promote | EX:30-40 | 8 lines a block | only at promote, at the end | until close | up to 4 parallel writers on one file; format error found last |
| `_gate/last-<mode>.txt`, `_tests/`, `baseline-failures.txt`, `_close/<slug>.log` | scripts | agents fixing findings, close | scripts | capped stdout | n/a | cleared by a passing close | ok |
| `retro.md` | `gates.sh retro` | nobody (close prints 5 findings) | close_gate.py:67 | 5 lines | n/a | cleared | ok since 68f47a0 |
| CHANGELOG entry | docs (step 5), promote completes it | surveyor K12, humans | prd-writing.md:55 | none | `gates.sh docs` | permanent | ok since one entry (68f47a0) |
| Agent return | each role | main | each agent's Return | 12 to 20 lines | **none** | context only | free text: `Gaps:` and "what is left" need interpretation |

Fields consumers need and do not get (the cause of rereads and exploration):

| Consumer | Needs | Missing from | Effect today |
|---|---|---|---|
| main on resume | tasks done, current wave and round, next action | `state.md` | reads `deliveries.md`, `impact.md`, `writing.md`; FAST phase 2 skipped the reviewer (AUDIT-v5 §2) |
| main after a return | gap route, who acts next | every return | classifies the gap itself (row 40) |
| main per High finding | within approved rules or not | reviewer return | reads diff or rules (FLOW-S8 call 31) |
| fixer executor | Owns, Read, rule rows | finding lines | explores |
| main after promote | files written, commit message, owner of each error | promote output | `git status`, `promote.py` reads (cluster A: 51 calls, 3.91M) |
| main after close | owner of each failing step | close block | routes everything to an executor |
| replacement agent | touched files, red tests, next step | free-text return | the main writes the handoff |

## 3. Return contract

Every role writes its return to `state/<slug>/returns/<step>.md` and runs `gate.py --return <file>` before ending (new check); the chat return is that file, at most 20 lines. The main acts on fields only and never verifies by reading.

```
Status: done | gap | blocked | ceiling
Step: <role> · <mode or task ID> · return check ok
Files: <paths changed, untracked included> | none
Commit: <message with Rules: or Case: trailer> | committed <hash> | none
Gate: <last line per step run> | none
Gaps: none | G1 · route user|short-c5|docs|executor|surveyor · <one line> · <path:line>
Ask: none | <question text ready for AskUserQuestion, options, recommended first>
Handoff: none | <Status ceiling only: touched files, red tests, next step; at most 6 lines>
Next: <the dispatch the main does next, from the table below>
```

Role fields added after `Gate:`: surveyor `Case, Size, Confrontation (block), Protected, Owner, Contexts, Fan-out, Change folder`, plus `Ask:` with the open-dimension questions; docs `Stopped: no|non-table|gate-red, Plan table, Waves (verbatim)`; executor `Task, Tests, Gate vs baseline, Lint, Delivery: deliveries/<T>.md`; reviewer `Round, Counts`, each finding `[Sev] CS-NNN · file:line · rule · scenario · fix · Act: fix|ask|pending · Owns: <files>`; recheck `CS-NNN resolved|open` lines, `New:`.

| Status | Main does |
|---|---|
| done, `Commit:` is a message | one commit Bash with `Files` and `Commit`, record due state lines, then `Next` |
| done, `committed <hash>` (docs) | record, then `Next` |
| gap, route user | ask with `Ask:` text; re-dispatch the same role with the answer |
| gap, route short-c5 | E08: surveyor short |
| gap, route docs, executor or surveyor | dispatch that role with the gap line and its evidence |
| blocked (missing prerequisite, tool or rate limit) | report to the user with the line; nothing else |
| ceiling | new agent of the same role with `Handoff:`; partial files stay uncommitted and are listed; second ceiling: brake (E17) |
| return check missing or failed | one re-dispatch asking only for the return file; never read the agent's files |

## 4. Leak map

| # | Leak | Evidence | Sev | Fix |
|---|---|---|---|---|
| L1 | Light route done inline (C1 to C4, C6) | SK:22,32; CL:9 | High | surveyor `light` mode (sonnet): rows, verdict, divergence block |
| L2 | No owner for the C3, C6, one-task C2 card | EX:10; SK:23 | High | `light` writes `card.md`, checked by `--step plan` |
| L3 | Step 4 and short C5 rule wording and `--rules` repair by the main | INT:5; EXE:27-28; LS25; AUDIT-v5 cluster B (71 calls, 4.6M) | High | docs `rules` (scribe): answers in, rows, DEC rows, gate, read-back block out |
| L4 | "Third failure is a gap, resolved first" with no owner | SK:16; AUDIT-prd-flow §2 (33 main gate runs, 4 gate-source reads) | High | `Gaps:` route field plus row 52 |
| L5 | Promote errors other than Source, and the promote commit | promote.py:293,315,339,355; EXE:43; AUDIT-v5 cluster A, 5 hand PRD edits | High | promote prints `owner:` per error, `files:` and `commit:`, or commits itself |
| L6 | Verification by the main (diff, source reads) | AUDIT-v5 §1: 9 diff or source reads; FLOW-S8 call 31; FAST-S7 read 7.7k of source | High | reviewer `Act:`; commit script checks the tree |
| L7 | Resume rereads agents' files | SK:52 vs SK:13 | Medium | `state.md` `Done:` and `Next:`; resume reads only state.md |
| L8 | High "fits the approved rules" judged by the main | SK:47; REV V04 | Medium | reviewer `Act:` |
| L9 | Commit check blind to untracked and unlisted files | EXE:17 | Medium | `gates.sh commit <slug> <task>` with `git status --porcelain` against `Files` |
| L10 | Parallel executors append to one `deliveries.md` | EX:28; EXE:15 (4 per wave) | Medium | `deliveries/<T>.md` per task; promote globs |
| L11 | Fixer with no Owns or Read | EX:10; REV V10 | Medium | finding `Owns:` becomes the fix card |
| L12 | Plan adjustments and red step-6 gate land on the main | AP:87; SK:13,42 | Medium | docs re-dispatch; add `changes/` edits to the never-list |
| L13 | Short C5: stop, stopped card, wave table refresh | EXE:26-28 | Medium | let running tasks finish, discard by patch; docs `short` rewrites cards and the table |
| L14 | Close failures without owner (trailers, G19, G21, baseline) | close_gate.py:86-96; gate_plan.py:133-150 | Medium | close prints `owner:` per failing step; baseline missing is `blocked` |
| L15 | Ceiling handoff written by the main | EXE:37 | Medium | `Status: ceiling` with `Handoff:` |
| L16 | `state.md` multi-writer, no validator | SV:30; SK:12; DO:21 | Medium | owner per section; `gate.py --state` |
| L17 | Prompt assembly by hand (cards, reviewer lines) | EXE:9,15; RV:10 | Low | `gate.py --wave <n> --prompts` prints executor and reviewer prompts |
| L18 | Main loads `repo.md` (7.2 KB, mostly worker data) and `interview.md` (9.6 KB) | SK:11 | Low | main-only section of repo.md; question format in the card |
| L19 | Shared PRD and consumer handoff without owner | IMP:15,20; AP:39 | Low | docs writes `handoff.md`; main relays with `Ask:` |
| L20 | Closing duplicates and retro rereads | AUDIT-v5 §1 (9 compare, 9 retro rereads) | Low now | fixed in SK:13 and close; keep the metric |

## 5. Enforcement

| Mechanism | Enforced mechanically today | Only written |
|---|---|---|
| Artifacts | `--pack`, `--rules` (Q2 to Q5), `--applied` (Q4), `--step prd|trd|plan` (Owns, IDs, P7 overlap), `--change`, `--final`, promote Source parse, `gates.sh trailers`, close requires a baseline | `state.md`, `impact.md`, `decisions.md`, `writing.md`, card fields beyond Owns, `deliveries.md` before promote, wave-table copy |
| Agent behavior | none at runtime | ceilings, rerun caps, read budgets, never-lists, return formats, single writer, no subagent |
| Main behavior | eval only: `protocol.py` `dispatch_map` and `main_violations` (edits, reads before surveyor, worker reads, extra gate runs, diff reads, source reads, kit reads, agent-file edits, retro reads) | owner of every failure, commit pattern, no ToolSearch or TodoWrite, plan by range, resume procedure |

Metric blind spots: `WORKER_ONLY_RE` still matches `reference/workers/` and misses `impact.md`, `classification.md`, `agent-plan.md`, `prd-writing.md`, `trd-planned.md` (protocol.py:27); agent files count on edit, not on read (protocol.py:41,251); `git status|log` is not counted; `PRE_EXEC_CMD` lets the main run `related`, `lint` before the first executor (protocol.py:33,155) although SK:13 forbids it; promote reruns are not counted; in C2, C3, C6 allowed light-route reads count as `reads_before` (no surveyor), so the category mixes allowed and forbidden reads.

Cheap mechanical enforcement (no hooks):

| # | Check | Where | Runs | Catches |
|---|---|---|---|---|
| N1 | `gate.py --return <file>`: fields, Status and route enums, `Files` changed in the tree, trailer in `Commit` | gate + every agent's last step | producer, before returning | free-text returns, L4, L6, L15 |
| N2 | `gate.py --state`: sections, owner per section, phase enum, `Done:`, `Next:`, wave table equal to `--step plan` output | gate | docs (step 8), main's commit Bash | L7, L16, stale table |
| N3 | Plan gate errors for every card field, card at most 25 lines, `Decisions:` IDs in `decisions.md`, `Leave:` items in pack Divergences, `Read:` paths exist; drop `Reviewer:` | gate_plan.py | docs | AUDIT-v5 §2 and §5 misreads, L11 |
| N4 | `gate.py --deliveries <T>` per task file | gate | executor | late promote failure, L10 |
| N5 | `gates.sh commit <slug> <task>`: porcelain vs `Files`, trailer, appends `Done: <T>` | script | main (one call per return) | L9, L6 |
| N6 | `owner:` and dispatch line on every promote and close error | promote.py, close_gate.py | scripts | L5, L14 |
| N7 | Eval categories: `main_agent_file_reads`, `main_git_inspect`, `main_state_edits_outside_own`, `main_gap_work` (tool calls between a gap return and the next dispatch or ask, other than record), `main_plan_whole_read`, `main_toolsearch`, `light_route_inline`; fix the regexes above | protocol.py | eval | every leak, per category in the report |

Hook option (not recommended): a PreToolUse hook on the main thread denying Read and Edit outside an allowlist and `git status|log|show`. For: the only runtime guarantee, it works outside the eval. Against: the maintainer prefers no hooks; per-machine settings and a Windows bash dependency; a denied call makes the model try another tool (more turns, LS27 shows rules get argued around); main versus subagent detection depends on the harness; hard to test offline. Producer-side gates (N1 to N6) plus the eval (N7) give most of the effect.

## 6. Ranked changes

| # | File | Exact change | Closes | Metric that should move |
|---|---|---|---|---|
| 1 | five agent files, SK main card, `gate.py` (`--return`) | Return block of section 3 in each agent; card line "act on fields; a failed return check is re-dispatched, never read"; Status table in SK | L4, L6, L8, L15 | `main_gap_work` 0; `main_source_reads`, `main_diff_reads` 0; main calls per return 1 |
| 2 | `promote.py`, `close_gate.py`, SK:14, EXE E20 | Print `owner: executor|docs|user` and the dispatch line per error; promote prints `files:` and `commit:` (or commits itself); baseline missing returns `blocked` | L5, L14, rows 51 to 60 | `kit_script_reads` 0; closing-phase main tokens about -1M per run in failing runs |
| 3 | SV, SK light route, CL C1 to C4 | Surveyor `light` mode: rows by ID, Source verdict, divergence block, `Tasks: 1|n`, `card.md` for C3, C6, one-task C2 | L1, L2, rows 4, 5, 7, 8 | `light_route_inline` 0; main tokens in C2, C3, C6 scenarios |
| 4 | DO (new `rules` mode), INT:5, SK step 4, EXE E09, E10 | Main records answers in `interview.md` Answer cells only; scribe writes rows, Example, conflicts, Supersedes, DEC rows, runs `--rules`, returns the read-back block; maintainer decision: one extra agent per read-back | L3, rows 15, 17, 18, 44, 51 | interview-phase main calls (cluster B) and tokens; `--rules` reruns by main 0 |
| 5 | SK State, EXE E01, DO step 8, `gate.py --state` | `state.md` sections with one writer each; `Done:` and `Next:`; phase enum; resume reads only state.md | L7, L16, rows 39, 46, 47 | phase-2 restart calls; `dispatch_map` 1.0 in FAST; `main_agent_file_reads` 0 |
| 6 | EX step 7, EXE E21, `promote.py` | `deliveries/<T>.md` per task; executor runs `--deliveries`; promote reads the folder | L10, late promote failure | promote errors 0 per run |
| 7 | `gates.sh` (`commit`), EXE E05, SK:12 | One script call per return: porcelain against `Files`, trailer, `Done:` append, one line out | L9 | main calls per return 1; stray paths at close 0 |
| 8 | `gate_plan.py`, AP card format | Every card field an error; card length; DEC IDs exist; Leave in pack; Read paths exist; drop `Reviewer:` | misread cards (AUDIT-v5 §2, §5) | `review_weighted`, `first_pass`, `prd_fidelity` |
| 9 | RV return, REV V04, V10, EX fix mode | Finding carries `Act:` and `Owns:`; the fix card is the finding lines plus Owns | L8, L11 | rework actions; fixer tool calls |
| 10 | `gate.py` (`--wave <n> --prompts`), EXE E04, E06 | Prints each executor prompt (card by range) and the reviewer prompt (rules, DEC, Leave, Lens of the wave) | L17, rows 28, 32 | main calls per wave |
| 11 | SK:13, AP:87, SK step 6, EXE E08 to E10 | Never-list adds `changes/` edits; plan adjustment and red step-6 gate go to docs; docs `short` rewrites stopped cards and the wave table; running tasks finish and are discarded by patch | L12, L13, rows 22, 25, 42, 45 | `main_state_edits_outside_own` 0 |
| 12 | `eval/protocol.py`, `eval/report.py` | N7 categories, fixed `WORKER_ONLY_RE`, read-side agent files, `git status|log`, no main `related` or `lint` before executors, promote reruns | measurement of all leaks | `main_violations` counts real leaks only, per category |

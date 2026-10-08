# Lessons (LS)

What was measured or broke in the source repository, and which rules came out of it. Read this when someone asks "why is this rule here?" or proposes removing one.

| ID | What happened | Rules it produced |
|---|---|---|
| LS01 | Moving the rule-change route from "main thread does everything" to "main thread conducts, workers write files": end-to-end time -48%, cost -53%, main-thread context peak from 196k to 76k tokens, same quality | SA01 to SA07, CE19 |
| LS02 | Every real session started at about 76k tokens of context and every subagent at about 41k, before doing anything | CE18: keep always-loaded files lean |
| LS03 | Workers were not worth it for tiny tasks (a small stale-PRD fix) or for a session that stops at the confrontation: the light route matched no-skill speed | Light route for C1 to C4 and C6; workers only in C5 and multi-task execution |
| LS04 | With a strong `AGENTS.md`, the baseline without the skill already scored 92% vs 96% with it. Most of the value is in the repo docs, the skill adds routing and discipline | `/ai-kit install`, then `/prd-create` and `/trd-create` before the first `/prd-flow` |
| LS05 | A proposed custom context-extraction CLI cost about the same tokens as native Grep (420 vs 440) and added fixed prompt cost and maintenance; it was rejected | CE11 |
| LS06 | A review loop without a ceiling consumed about 3.6 of 8.8 agent hours in one delivery ("eternal loop"); the review itself was valuable | RV01 to RV10, ceiling chosen by the user: 5 rounds |
| LS07 | One executor reached about 300k tokens and 150 tool calls, costing more than the rest of the route | SA15, SA16, SA19 |
| LS08 | One delivery spent about 7.5M subagent tokens, mostly in rereads and review loops | SA03, SA22, CE16, RV03 |
| LS09 | Agents took 13 to 14 minutes per task because each ran the whole unit suite (4 to 5 minutes) and retyped thousands of lines; parallel agents broke each other's test collection | TS02, TS03, SA26, SA13 |
| LS10 | The user corrected "run only the mirror test" to "run the tests related to the file": mirror plus importers | TS02 |
| LS11 | Splitting giant files and giant test files is what makes related-test runs cheap: modules over 500 lines went from 18 to 1, long functions from 43 to 1 or 2, `nonlocal` from 62 to 0, test files over 1,200 lines from 11 to 0; a 4,056-line class became 23 collaborators | AR01 to AR18 |
| LS12 | Writing markdown and HTML through Python scripts slowed the writer noticeably; the user asked to stop | SA11, WS07 |
| LS13 | A hand-maintained 440 KB HTML PRD would have dominated any context that read it | CE05, DS14: the HTML stays for people and agents never read it |
| LS14 | Plans that grew past 60 KB were paid on every executor read | CE16 |
| LS15 | A run reported the full-suite number as the offline number because a database variable leaked from an earlier command; the two equal numbers looked like confirmation | TS12, TS13, TS20 |
| LS16 | After moving tests beside the code, 119 tests ran without the offline guard and with agent switches on, because the autouse fixtures lived in a nested `conftest.py` | TS18 |
| LS17 | Patches targeting the old monolith module silently stopped having effect after the split | TS17, AR11 |
| LS18 | A package `__init__` that mounted routes or imported the engine closed an import cycle | AR08 (re-export only; no side effects in the public entry) |
| LS19 | The shell output proxy (RTK) swallowed test and lint output, causing retries | CE14, TS08 |
| LS20 | Docs were often stale: files cited that no longer existed, env vars removed, "implemented" rules with no caller | DS04, DS13, the F2 check of the skill |
| LS21 | Code fallbacks that chose the next question or skipped steps on agent failure produced the redundant questions the agent was built to remove | CX07 |
| LS22 | The skill was evaluated with headless runs in separate worktrees, one per scenario and per version (no skill, v1, v2), graded against expectations, with time and cost per run. That is how the -48% and -53% of LS01 were measured, for about US$18 of eval spend | MAINTAINING.md "Evaluating the skill" |
| LS23 | Mid-execution decisions that removed a safety net were slipped in as "one more task" and escaped the review | RV06, WF12, WF20 |
| LS24 | prd-flow round 2026-10-07 (small fixture, S5 to S7, one rep each, `eval/results/2026-10-07-flow/report.md`): against prd-gate it left no live contradiction (S5: 0 versus 1), delivered the open-dimension scenario completely (S7: 7 of 7 hidden tests versus 4 of 7), had no blind-review bug and 1 tool error versus 8, but cost US$18.38 versus US$11.53 and 53 versus 33 minutes. The main thread ran the surveyor, writer and planner sections inline (2 subagents versus 6 on S5; main-thread tokens 4.7M to 6.3M versus 2.0M to 2.8M) | prd-flow SKILL.md "Worker": steps 2, 5, 7 and 8 always dispatched |
| LS25 | Second prd-flow round (`eval/results/2026-10-07-flow-v2/report.md`): with the workers dispatched, main-thread tokens fell to the prd-gate level (8.7M versus 7.4M) and S5 cost US$5.79 versus 5.47, but in all three runs the main thread wrote `interview.md` and `approved-rules.md` free-form without reading `reference/interview.md`; the `writer-prd` hit Q2/Q3, rewrote them, then hit Q4 because the approved rows lacked the marker and Source `planned`, and became the most expensive worker (1.3M to 2.0M tokens) | prd-flow SKILL.md step 4 and "Formats of step 4"; workers.md writer-prd step 1 |
| LS26 | Wall time of the second round, per agent (S5): writer-prd 5.4 min (format loop), writer-trd 1.8 and planner 1.4 as two agents, three serial executor tasks of 1.0 to 2.6 min with Promote as its own agent; the main thread itself took about 8 minutes in both versions. Each agent pays a cold start of about a minute rereading the same files, so the time grew with the number of serial agents, not with the work. Two of three runs also skipped the reviewer | SKILL.md "Worker" (steps 7 and 8 in one agent); agent-plan.md (split only for parallel work, Promote inside the last task of a small plan); execution.md E04, E06 |

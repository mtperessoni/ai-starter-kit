# Session slowness audit, 2026-10-14

Scope: every Claude Code session since 2026-10-01 under `~/.claude/projects/c--Projects-agora-consulta-fe` (it holds the work on agora-consulta-fe, clara-ai, modulo-integrador and ai-starter-kit), the telemetry in `agora-consulta-fe/.ai-kit/runs/`, and the test suites of the four repositories. The scripts that produced every number are in `scripts/`. The detailed test audits are `audit-kit-fe-tests.md` and `audit-clara-tests.md`.

## Verdict

The process became most of the workload. Tests are the largest tool cost inside it, not the root cause. "Rigged tests" holds only for the kit.

## F01 to F12

| ID | Finding | Evidence |
|---|---|---|
| F01 | Long sessions are orchestrations of 70 to 121 subagents; implementation is a minority of dispatches | ecde3293: 115 dispatches (49 docs, 36 implement, 22 review). d012bb2c: 121 (50 docs, 28 implement, 27 review, 15 fix). 33d0c972: 100 (75 review or recheck, 9 implement). `disp.py`, keyword classification |
| F02 | Subagent active time: docs 45%, review 32%, implementation 14% | 54.7 h docs, 38.8 h review, 17.4 h implement (gaps capped at 15 min). `docs.py` role heuristic |
| F03 | Only 24% of agent file writes hit product code | 18,000 Edit/Write calls: product 24%, kit 20%, PRD/TRD/changes 17.5%, tests 16%, scratch 10%, `.claude`/state/gates 9.6%. `where.py` |
| F04 | Product work is short when it happens | conversation-reconnect product commits: 37 min (2026-10-09 16:38 to 17:15) inside a 4.5 h run. sara-speech-boundary FE commits: 3 h |
| F05 | Wall clock includes hours blocked on AskUserQuestion | 9528886a 19 h of 20.7 h; bc48964b 6.9 h of 10.4 h; 3880e4ef 2.6 h; 19b4481d 2.3 h; 720e2b35 2.2 h. `wall.py` |
| F06 | Test execution: about 31 h in two weeks, about one third of subagent active time | clara-ai about 12 h, kit about 9 h, FE about 3 h. `tests.py` |
| F07 | Kit tests are self-referential ("rigged") | 85 to 90% of kit test files test the process itself; 98% of commits touching tests also touch implementation; 100 to 150 literal-prose assertions; subprocess per test (`test_kit_gates_run_speed`: 49 tests in 174 s) |
| F08 | clara-ai tests are slow, not rigged | Starlette TestClient websocket tests about 3.5 s each (idle loop waits); real sleeps in 37 files; coverage on by default (pyproject.toml:215); no xdist; serial unit suite over 10 min, hence the 600 s timeouts. Baseline red: 2 failures; default gate.py fails with 2 G7 |
| F09 | Agents edit tests to get green | After a failing run, 22% of the next edits touched a test file (15% only the test); 16% of agents had 3 or more consecutive failing runs (max 20). `loops.py`, failure detection by regex |
| F10 | Rules exist but are only detected after the fact | Polling loops about 4 h; full suite mid-task 11 times in one run; 17 subagents over 150k tokens (max 495k) |
| F11 | General-purpose subagents inherit Opus 1M at high effort | 47% of subagent turns ran on Opus despite "sonnet by default". Turn latency barely grows with context (p50 2 to 4 s); cost is turn volume (about 20,000 subagent turns) |
| F12 | Smaller overheads | Edit about 1.2 s each (IDE and hooks), serialized when batched: 4 to 5 h. FE `gates.sh one` 12.6 s average vs about 4 s for vitest direct: about 7 Python spawns plus the Storybook plugin loaded for unit runs |

## Docs findings (D01 to D06)

| ID | Finding | Evidence |
|---|---|---|
| D01 | Doc cost is reading and syncing, not writing | clara-ai since 2026-10-01: PRD 9.6k + TRD 7.4k + CHANGELOG 1.3k changed lines, against about 55 h of docs-agent time |
| D02 | The docs gate fails a third of the time, on bookkeeping | 459 gate runs by docs agents, 166 failing (36%). Top codes: G5 and G29 (HTML stale), G2 (INDEX row and IDs column), G9, G31 (section budget), G7 (CHANGELOG line per reworded rule), G23 (TRD path) |
| D03 | One rule change fans out to many synced copies | PRD row, INDEX IDs column, CHANGELOG line, TRD row, area CLAUDE.md, HTML page, decisions.md, plan.md, state.md, module and test ID headers, commit trailer |
| D04 | Living docs are large and reread whole | clara-ai PRD tree 125 files and 831 KB (about 200k tokens), TRD 391 KB (voice.md 68 KB), CHANGELOG 173 KB; prd-flow state.md 358 KB read over 26 reads in one change; 691 same-file rereads by docs agents |
| D05 | Docs agents run on Opus and are redispatched per adjustment | `prd-flow-docs` is `model: opus` in the three repos; d012bb2c dispatched it 26 times |
| D06 | FE and BE line churn is mostly the kit itself | Process files are 40% of FE and 53% of modulo-integrador changed lines since 2026-10-01 |

## Corrections made during the audit

- The median Edit of 5.2 s was queueing of batched Edits; a solo Edit is 1.2 s.
- The 47k lines under clara-ai `specs/012` are one data file (`question-bank/tmp_assessment_question.json`), not docs.

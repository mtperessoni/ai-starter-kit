# Audit: prd-flow end to end, why a plain agent beats it (2026-10-09)

Status: diagnosis. Complements [`AUDIT-prd-flow-run-2026-10-09.md`](AUDIT-prd-flow-run-2026-10-09.md) (interview, gates, orphans of one run) and [`../proposals/plan-interview-one-pass.md`](../proposals/plan-interview-one-pass.md). This file does not repeat their findings; it looks at the architecture that produces them, measures it, and checks what branch `feat/one-pass-interview` (HEAD `0f86bb4`) still leaves open. Nothing in `kit/` was changed.

## 0. Verdict
prd-flow is slow because of its shape, not because of one bad rule. It moves every piece of understanding through cold agents and files, writes the same rule four or five times, then runs scripts that check those copies against each other. A plain agent ("read what changed in the PRD and implement it") keeps the user's conversation, reads the code once, writes the rule once and wires the feature end to end. The one-pass interview fixes the worst loop (the 16 dimensions and the question rounds), but leaves the rest of the shape in place: the serial surveyor to docs pipeline on opus, about 20 artifact types per change, 58 gate codes, and agent ceilings lower than the work the protocol assigns them. Three orphan and leak paths are still open.

| # | Root cause | Share of the cost (measured) |
|---|---|---|
| RC1 | The chief, the only agent that holds the user's intent, is forbidden to use it; every agent restarts cold | 89 prd-flow agents for one feature in 3 repos (session d012bb2c) |
| RC2 | The documentation phase generates more text than the code phase | docs: 394k output tokens versus 123k for every executor together (d012bb2c) |
| RC3 | The protocol writes a rule 4 to 5 times and checks the copies with scripts | 58 gate codes, 21 gate flags, about 8,000 lines of governance code |
| RC4 | Ceilings below the assigned work, so handoffs and cold restarts are designed in | 8 of 26 docs agents and 4 of 10 surveyors past 50 calls |
| RC5 | Cards cut a feature into Owns slices, so wiring and intent get lost and redone | T05 and T01/T02 redone, T08 shipped unwired, T08b added; 5 of 5 review rounds |
| RC6 | The kit is a moving target that was never measured against a plain agent | 87 kit commits in 2 days; 3 repos on 3 different versions; no control arm in `eval/` |

## 1. Sources
| Source | What it gave |
|---|---|
| Kit at `feat/one-pass-interview` `0f86bb4`: `SKILL.md`, `repo.md`, 9 references, 5 agent files, `settings.json`, `scripts/` | Current instructions, hooks, gates, reaper, watchdog |
| Session `d012bb2c` (10-08 19:13 to 10-09 11:12): `assessment-single-agent` (clara-ai), `assessment-categories-front` (fe), `assessment-categories-contract` (be); 121 subagent transcripts | Phase timeline, tokens and calls per role, dispatch prompts |
| Session `f57d6438` (10-09): 45 subagent transcripts | Same measures, second run |
| `.ai-kit/runs/*/events.jsonl` of fe, clara-ai, be | Alive time against tool time, reads by kind, gate runs, heredocs |
| fe `changes/003-conversation-reconnect/retro.md`; `ai-kit.json` of the three repos; state folders and run folders on disk | Repeated big reads, disk leftovers |
| `eval/arms*.json`, `eval/arms/` | What the eval compares |

Method: the scripts in this session's scratchpad (`runs.py`, `turns.py`, `skeleton.py`) read the transcripts' `usage` blocks (input, cache read and cache creation summed per turn) and the telemetry events. "Input" below is the sum over turns of the context sent, the number that drives latency and cost.

Limits: no real run used the one-pass branch yet (it landed 10-09 18:46 to 18:53); every number is from the version before it. The installed `SKILL.md` of fe, clara-ai and be differs from the kit HEAD.

## 2. Headline numbers
| Measure | d012bb2c | f57d6438 |
|---|---|---|
| prd-flow agents dispatched | 89 (plus 32 kit-work agents) | 45 |
| Input tokens, docs plus surveyor | 288M | 112M |
| Input tokens, executors | 166M | 91.5M |
| Output tokens, docs plus surveyor | 489k | 176k |
| Output tokens, executors | 123k | 141k |
| Agents past 150k context | 12 prd-flow (6 docs, 3 surveyor, 3 executor) | 7 |
| Agents past the 50-call ceiling | docs 8/26, surveyor 4/10, executor 7/41 | docs 4/9, surveyor 3/5, executor 7/23 |
| Start of survey to first executor (clara-ai slug) | 19:15 to 21:35, 2 h 20 min | about 40 to 55 min per slug (earlier audit) |
| AskUserQuestion before code (clara-ai slug) | 9 calls, 29 questions | 12 calls in 28 min |
| Executors alive past their work | 3 at about 766 min for 3 to 6 min of tool time | 6, about 230 min total |

What a docs agent does with its calls (d012bb2c, 26 agents, 1,306 calls): PRD rows 29%, TRD 9%, CHANGELOG and INDEX 2% (product writing, 40%); state files (`approved-rules`, `interview`, `state.md`, `pack`, other) 15%, gate and render scripts 7%, kit instructions 6%, change folder 5%, commits 2% (protocol, 35%); the rest is shell reads.

## 3. Why a plain agent wins: root causes
### RC1 The chief cannot use the context it has
| Mechanism | Where | Effect |
|---|---|---|
| The chief reads only `repo.md`, `dispatch.md`, the sheet and cited rows; DP01 forbids any domain reading in a prompt | `SKILL.md` "Chief card", `dispatch.md` DP01 | The conversation, where the user already explained the problem, never reaches an agent except as verbatim `Decided in conversation:` lines |
| Every role is a new agent: surveyor, docs, executor per card, reviewer per wave, fix, recheck, close | `SKILL.md` "Cases", "Returns" | Each starts at about 24k tokens and rebuilds the picture from files: repo adapter, references, PRD rows, TRD, code |
| The same facts are read by every hop | `turns.py` | In d012bb2c surveyors read 191 KB of source, docs 32 KB, executors 203 KB, plus 306 KB of kit instructions and 244 KB of state files across roles |

A plain agent pays the cold start once, keeps the conversation, and reads each file once.

### RC2 The expensive phase is serial, on opus, and text-bound
| Step | Model | Parallel? | Measured |
|---|---|---|---|
| Surveyor `full`: classify, proof F1 to F3 per rule, sweep K01 to K14, `pack.md`, `sheet.md`, gates `--pack`, `--snapshot`, `--sheet` | opus | no | 37 to 118 turns, peaks 91k to 184k |
| User reads the sheet | | | |
| Docs `apply`: `answers.md`, `rules.md`, `decisions.md`, render, PRD rows, CHANGELOG, INDEX, README, ADR, TRD Planned, `brief.md`, `design.md` (L), `plan.md`, `## Plan`, gate, 3 commits | opus | no (fan-out only past 2 contexts) | 95 to 232 turns, peaks up to 244k, one agent at 35M input |
| User approves | | | |
| Waves | sonnet | yes | 60k average peak, cheap |

Parallelism sits where the work is already cheap (executors); the critical path is two opus agents writing prose. 394k output tokens of docs in d012bb2c is roughly 1.5 to 2 hours of pure generation at typical speed, most of it on the critical path. The earlier audit measured the same thing from the other side: 32 min wall for 71 s of tool time in one docs agent.

### RC3 One rule, many copies, scripts to reconcile them
A C5 rule today travels: request, `pack.md` (literal row), `sheet.md` (Today and Becomes), `answers.md`, `rules.md`, `approved-rules.md` (rendered), PRD row with `*(approved, pending code)*`, CHANGELOG reason, TRD Planned row, plan card `Contract:`, `deliveries/<task>.md` `Source:`, promote (marker out, Source in, old text to CHANGELOG, Planned merged into the TRD body, folder archived).

| Artifact kind | Count per C5 |
|---|---|
| Files in the state folder | `state.md` (4 writers), `pack.md`, `sheet.md`, `sheet-2.md`, `answers.md`, `rules.md`, `approved-rules.md`, `facts.md`, `card.md`, `deliveries/*`, `findings-r*`, `msg-*.txt`, `baseline.status`, `compare.status`, `final.log` |
| Files in `changes/NNN-<slug>/` | `decisions.md`, `brief.md`, `design.md`, `plan.md` |
| Living docs touched twice | PRD rows (marker, then promote), TRD (Planned, then merge), CHANGELOG (entry, then excerpts) |

The gates then check these copies against each other: 58 codes (G0 to G32, P1 to P17, Q1 to Q5, S0 to S6) behind 21 `gate.py` flags, about 8,000 lines of Python and shell in `kit/scripts` and `prd-flow/scripts`. Most codes check consistency between protocol artifacts (sheet against pack, answers against sheet, plan against TRD), not product behavior. Every red code is another turn; d012bb2c docs agents ran the gate 31 times in 5 of them. A plain agent edits the PRD row once and git is the record.

### RC4 Ceilings below the assigned work
`review.md` V08 caps executor, surveyor and docs at about 50 calls. The minimum sequence of a docs `apply` for a one-PRD size M change, counted from `prd-flow-docs.md`: about 10 reads, 14 to 18 writes, 1 render, 2 gate runs, 2 to 4 fixes, 3 commits at 3 calls each (Write the message, `git add`, `git commit -F`, mandated by "one command per call" and the heredoc ban). That is 40 to 50 calls with nothing going wrong. A surveyor `full` with 10 rules needs batch 1, 3 proof calls per rule, at least 14 sweep calls, pack, sheet and 3 gate runs: 60 or more. The ceiling therefore triggers a handoff and a cold replacement by design, which is exactly the "agent passed 150k and was replaced" pattern in the numbers above.

### RC5 Cards lose the feature
| Mechanism | Evidence (d012bb2c, clara-ai) |
|---|---|
| Owns slices a feature by file; wiring belongs to "the last task" | T08 committed, but "a voz ainda não funciona de ponta a ponta... faltam três peças fora dos arquivos que eram dela"; T08b dispatched |
| A card carries IDs, not intent, so the executor falls back to reading the PRD broadly | executor `cd docs/prd/prd-3; cat 09-*.md 10-*.md 11-*.md 12-*.md 13-*.md`, then `cat 14-*.md ... 18-*.md` |
| A rule gap found mid-wave stops dependent tasks and reruns the survey | T05 crossing mark: short survey, docs, "Redo T05", "Redo T01 + T02" |
| Review per wave by a cold reviewer, fix by a cold executor, recheck by a third | 5 of 5 rounds used; 11 reviewers, 1 recheck, at least 8 fix agents |

A single implementing agent that owns the feature wires it as it goes and asks its question when it meets the gap, with the conversation still in context.

### RC6 Moving target, no control
| Fact | Evidence |
|---|---|
| Churn | 50 kit commits on 10-08, 37 on 10-09; the guard hook was dropped at `9a17533` (10:58) and re-added at `3d2f647` (18:46) |
| Version skew | `SKILL.md` installed in fe, clara-ai and be differs from the kit HEAD; a cross-repo dispatch tells the agent "if `<target>/.claude/agents/prd-flow-executor.md` exists, follow it over your default file", so one agent holds two versions of its own definition |
| No control arm | `eval/arms*.json` compare kit against kit (GATE against FLOW, spec-kit against living). No arm runs a plain agent on the PRD diff, the thing the user reports as better. The interview is never exercised (0 questions in 19 eval transcripts) |
| Telemetry not trusted | fe `retro.md` of conversation-reconnect reports `Subagents: 0`, `tokens_main: n/a` for a run with 23 subagents, and was committed to the repository with 25 `big_output` lines |

## 4. Context flooding map (current branch)
Static instructions are not the main flood: a prd-flow agent starts at 22k to 26k tokens. The flood is turn count times a context that grows with every artifact written and every whole-file read.

| ID | Flood | Size | Fix |
|---|---|---|---|
| CF1 | Ratchet `allowlist` inside `ai-kit.json`, the file agents read for commands and the interpreter | fe 58.6 KB (48.9 KB allowlist), be 114.7 KB (100.8 KB allowlist); one agent read it 4 times at 61 KB | Move the allowlist to `scripts/ratchet-allowlist.json`; `ai-kit.json` stays under 5 KB |
| CF2 | `repo.md` read by every role (162 lines), mostly gate-config prose and placeholders the agents do not need | 8.5 KB per agent | Split: `repo.md` keeps Commands, Layout, Protected rules, Change routing for agents; Gate config moves to a file only the scripts parse |
| CF3 | Always-loaded project context in every subagent carries three competing workflows | fe `AGENTS.md` describes spec-kit, `/orchestrate` and prd-flow; fe `CLAUDE.md` tells every agent to read the stale `specs/008-unit-config-tokens-fe/plan.md` while `AGENTS.md` says `specs/` is never read | One workflow in the always-loaded files; drop the `specs/008` pointer |
| CF4 | Cross-repo agents receive two definitions of themselves (RC6) | 8 to 11 KB duplicated, possibly contradictory | Run the chief from the target repo (or its worktree); never "follow the other file" |
| CF5 | The docs agent reads 6 to 7 references in `apply`: `interview.md`, `prd-writing.md`, `trd-planned.md`, `agent-plan.md`, `anatomy.md`, templates | about 50 KB before writing | One `apply` reference of at most 150 lines with only what `apply` writes |
| CF6 | 109 cross-referenced rule IDs across 14 runtime files (E 23, K 14, DP 13, G 10, V 10, C 7, BR 7, TP 7, S 6...) | 1,141 lines, 126 KB | Agents follow imperative steps; IDs live only where a script or a test needs them |
| CF7 | Gate output the agent must read and ignore (G25, G29, G32, G28 warnings) | earlier audit: G25 printed 111 times across 15 agents | Print only errors to agents; warnings go to the close report |
| CF8 | State and run folders never cleaned | clara-ai: 19 state folders, 7.4 MB; fe `.ai-kit/runs` 7.6 MB with loose `t02.log`, `fix.out` files; surveyors `cat state.md && cat approved-rules.md && cat impact.md && cat interview.md && cat pack.md` | `gates.sh doctor` lists stale state folders; a slug that never closed is archived or deleted on the next run |

## 5. Slowness map
| ID | Where time goes | Evidence | Fix |
|---|---|---|---|
| SP1 | Two serial opus agents before any code (RC2) | 2 h 20 min to the first executor in d012bb2c | Default path without them (section 8) |
| SP2 | Generated prose: the PRD, TRD Planned, brief, design, plan, cards, CHANGELOG, `## Plan`, `answers.md`, `rules.md`, `decisions.md` | 394k docs output tokens against 123k code | Write the PRD row once; no TRD Planned, brief or plan for a change under about 5 tasks |
| SP3 | Turn inflation from "one command per call" and commit via message file | 3 calls per commit; docs agents commit 3 times | Test whether the permission classifier accepts `git add <paths> && git commit -F <file>` (the earlier audit saw `&&` chains with `-F -` blocked); if it does, allow it in one call |
| SP4 | Ceilings below the work (RC4) | cold replacements | Raise ceilings to match the protocol or cut the protocol |
| SP5 | Review per wave plus fix plus recheck, all cold | 5 rounds in d012bb2c | One review at the end on the whole diff, fixes by the implementing agent (resumed with SendMessage), at most 2 rounds |
| SP6 | Hooks: 12 events, each launching bash, sed, a `python -c pass` probe and the script; plus the synchronous guard hook on every agent Bash | 5,422 events in one run, about 20k process launches; the G11 fix ("no probe") is not in `settings.json` | Write the resolved interpreter path into the hook command at install; drop the probe; record only Pre and Post tool, Subagent start and stop |
| SP7 | Full suite and baseline machinery (`baseline.status`, `compare.status`, content-hash cache, rerun of failing ids) for every slug, including small ones | earlier audit: about 177 min of full-suite time in one day | Small changes run related tests only; the full suite runs in CI |

## 6. Orphans and leaks: status after the branch
| ID | Path | Status | Evidence | Fix |
|---|---|---|---|---|
| LK1 | Heredoc and stdin interpreters hang a shell past the agent | Fixed for prd-flow agents (`guard_hook.py` in their frontmatter) | | Keep |
| LK2 | Executor, reviewer and recheck are told to put long commands "in the background, woken by the completion notice". A subagent is not woken: it returns, and the shell outlives it ("stopped with background work of its own still running"), or it polls | **Open** | d012bb2c executors ran `sleep 540; tail ... final.log` and `for i in $(seq 1 28); do ... sleep 20; done`; surveyor and docs say the opposite (foreground with a timeout) | Subagents never use `run_in_background`; foreground with an explicit timeout under 600 s; anything longer is the chief's |
| LK3 | Agents outside the guard: `dispatch.md` says "`prd-flow-<role>`, else `general-purpose` following its `.claude/agents` file", which drops the hook, the tool list and the model | **Open** | 31 general-purpose agents in d012bb2c ran up to 25 heredocs each | Remove the fallback; put the guard in `settings.json` `PreToolUse` for every agent, not only the prd-flow frontmatter |
| LK4 | The watchdog only writes `agent_stuck` to `events.jsonl`; `verify.py` reads it at wave end. Nothing acts mid-wave, and the chief "never polls", so a hung agent holds its wave forever. The scan also runs only when some hook fires | **Open** | 3 executors alive about 766 min (10-08 22:21 to 10-09 11:09) | The chief gets a per-wave deadline: after it, TaskStop the agents still running, `gates.sh reap`, redispatch with a handoff. Or a Monitor on the events file in the chief |
| LK5 | `reap.py` never kills a tree rooted at `gates.sh baseline`, `compare` or `verify`; those are the processes that hang (G1: pytest-timeout `os._exit`, suites dying at 40%) and they outlive the session | **Open** | `PROTECTED` regex in `reap.py` | Protect them only while their slug's `.status` says running and the age is under the run's timeout; otherwise reap |
| LK6 | Background task output files are never deleted | **Open** | retro `dead_files`: 3.7 GB in one session's `tasks/` folder | `gates.sh clean-outputs` in close and in the reap step |
| LK7 | State folders of slugs that never closed stay forever and are read by later agents (CF8) | **Open** | 19 in clara-ai | Doctor plus archive on the next run |
| LK8 | Cross-repo dispatch resolves the agent definition and its hook from the chief's repo while the agent works in another (CF4); `CLAUDE_PROJECT_DIR` points to the chief's repo | **Open** | d012bb2c prompts | Chief in the target repo or worktree |
| LK9 | Interpreter ambiguity invites fallback chains | Partly fixed (`gates.sh python`) | d012bb2c prompts said `Python: python` in one dispatch and `.venv/Scripts/python.exe` in another | Resolved once at install into `ai-kit.json` and the hook command |

## 7. What the branch already fixed
| Item | Effect |
|---|---|
| One decision sheet, one follow-up, one approval; 16 dimensions and gate Q3 gone | Removes the question loops (earlier audit D1 to D5, L1 to L8) |
| Surveyor writes only `pack.md` and `sheet.md` | Fewer scaffolds |
| Executor lints its own files; close runs lint before compare | Removes lint-only close failures |
| Guard hook, `gates.sh reap`, reap at every wave end, TaskStop on a "background work still running" notice | Closes LK1, most of the 230 orphan minutes |
| Chief may explain a sheet item with today's rule | Removes rephrased repeats |

Residual after the branch: RC1 to RC6, CF1 to CF8, SP1 to SP7, LK2 to LK9.

## 8. Recommendation: make the plain agent the default path
The evidence says the value of prd-flow is in three places: the literal rule text and its conflicting neighbors (sweep K01, K11, K14), the code proof of each touched rule (F1 to F3), and one approval of the rule diff before code. Everything else is transport. Keep the value, drop the transport.

### 8.1 Target flow
| Step | Who | What |
|---|---|---|
| 1 | Chief, in the user's conversation, with the skill loaded | Reads the touched PRD rows, their neighbors (K01, K11, K14) and the code that implements them (F1 to F3). Small and medium changes: no surveyor |
| 2 | Chief | Shows the rule diff (today, then new), what does not change, and at most 8 decisions with a recommendation, as one message; ends the turn |
| 3 | Chief | On the answer: edits the PRD rows (final text, once), the CHANGELOG entry with the decisions inline, the TRD area file when files move; one commit |
| 4 | Chief, or executors only when the work splits | Implements test first. Fan-out only when there are two or more independent areas of at least about 10 calls each; each executor gets a brief written by the chief that carries the intent, not only IDs |
| 5 | One reviewer | Reviews the whole diff once; the implementing agent fixes (resumed with SendMessage); at most 2 rounds |
| 6 | Chief | Related tests, lint, a small content gate, report |

Size L, cross-repo, or a new PRD keep the surveyor and the docs agent as today, because there the sweep is wide and the context is worth isolating.

### 8.2 Cut list
| Keep | Merge | Delete |
|---|---|---|
| Rule IDs, the literal Today text, the sweep K01, K11, K14, the proof F1 to F3, one approval, the CHANGELOG with decisions, tests citing IDs, the guard hook, reap | `answers.md`, `rules.md`, `approved-rules.md`, `decisions.md` into the CHANGELOG entry plus git; `brief.md` and `plan.md` into the chief's dispatch briefs; `pack.md` into the chief's context | Pending-code marker and promote rewrite (the change commit is the record); TRD Planned (the brief names the files); `deliveries/*` except when a task really consumes another's symbol; sheet lint S1 to S6, pack lint, plan alignment P11 to P17, Q-codes; per-wave review and the separate recheck agent; `Wave time`, the dispatch ledger in `state.md`; general-purpose fallback |

### 8.3 Gates after the cut
One `gate.py --final` with content checks only: every cited ID exists and is unique, every rule changed by the commit has a CHANGELOG entry, every code rule's Source symbol exists with a non-test caller, every new test cites an ID, no em dash. Errors to the agent, warnings to the report.

### 8.4 Fix list that does not depend on the redesign
| Item | Closes |
|---|---|
| Subagents never background; foreground with a timeout under 600 s | LK2 |
| Guard in `settings.json` for every agent; no general-purpose fallback | LK3 |
| Per-wave deadline in the chief, then TaskStop, reap, redispatch | LK4 |
| Reap protects suite trees only while their status says running and within their timeout | LK5 |
| `clean-outputs` in reap and close; doctor archives stale state folders | LK6, LK7, CF8 |
| Chief runs in the target repo or worktree; no "follow the other file" | LK8, CF4 |
| Allowlist out of `ai-kit.json`; Gate config out of the agent-facing `repo.md` | CF1, CF2 |
| One workflow in fe `AGENTS.md` and `CLAUDE.md`; remove the `specs/008` pointer | CF3 |
| Interpreter path written into the hook commands at install; no probe; fewer hook events | SP6, LK9 |
| `git add <paths> && git commit -F <file>` allowed in one call | SP3 |
| Ceilings match the assigned work, or the work shrinks to the ceiling | RC4, SP4 |
| Freeze the kit between measured releases; one version across the three repos | RC6 |

## 9. Prove it before rolling it out (M07)
Add a control arm and the missing scenario to `eval/`:

| Item | What |
|---|---|
| Arm `PLAIN` | No skill. Prompt: "the PRD changed in `<commit>`; read the diff and the code, implement test first, update the TRD if files move". Same fixtures, same hidden tests |
| Arm `LITE` | Section 8 flow |
| Arm `FLOW` | `feat/one-pass-interview` |
| Scenario with an interview | A request that needs 2 to 4 decisions, answered by a scripted user; one answer ambiguous |
| Scenario with a gap found mid-implementation | Measures the short C5 against the plain agent asking |
| Metrics | wall time, time to first code, input and output tokens per phase, agents dispatched, agents past 150k, hidden tests passed, rule conflicts caught (S7 kind), rules written that the user did not decide, user touchpoints, `stuck_minutes`, orphans at the end |

Adoption rule: `LITE` replaces `FLOW` when hidden tests and conflicts caught are not worse and wall time and tokens drop. If `PLAIN` matches `LITE` on quality, the skill should shrink further, to the sweep and the approval only.

| Target on the next real C5 (size M) | Measured before | Target |
|---|---|---|
| Time to first code | 40 min to 2 h 20 min | under 15 min of agent time after the answer |
| Agents dispatched | 45 to 89 | at most 6 |
| Docs output tokens / code output tokens | 1.2 to 3.2 | under 0.5 |
| Agents past 150k | 7 to 12 | 0 |
| Gate runs in the docs phase | 31 (5 agents) | 1 |
| Review rounds | 5 | at most 2 |
| `stuck_minutes`, orphans at the end, task output left on disk | 230 min, 7, 3.7 GB | 0, 0, 0 |

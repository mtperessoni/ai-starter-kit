# Audit: why prd-flow runs are slow and loop (real runs of 2026-10-08/09)

Status: diagnosis complete, fixes proposed in [`proposals/plan-interview-one-pass.md`](../proposals/plan-interview-one-pass.md); nothing in `kit/` changed yet.

## 1. Scope and sources
| Source | What it gave |
|---|---|
| clara-ai run of 2026-10-09 (another machine), slugs `voz-sempre-igual` (C5), `fala-duplicada` (C3), `sara-calada` (C3), commits `a1f1216a..b6f46280` on `origin/staging` | Docs history, the DEC-44 reversal, CHANGELOG growth |
| The pt-BR audit of that run (gates, close, telemetry; file `auditoria-lentidao-prd-flow-2026-10-09.md`) | Problems G1 to G15 in section 3 |
| Two real prd-flow sessions on this machine: `9528886a` (sara-welcoming-tone, 10-08 20:07 to 10-09 16:39) and `f57d6438` (voice-resilience, assessment-inference, conversation-reconnect, 10-09 18:56 to 20:45), 61 subagent transcripts, the chief's own audit at f57d6438 20:45 | Questions asked, gate failures, edits per file, instruction-induced misbehavior |
| clara-ai `.ai-kit/runs/*` telemetry | No gate output or question text (blind spot, section 8) |
| 19 eval transcripts (`clara-ai-evals-*`) | 0 questions to the user, at most 2 gate errors: the eval never exercises the interview |
| The kit itself: `SKILL.md`, every `reference/*.md`, the five `prd-flow-*` agents, `kit/CLAUDE.md`, `kit/AGENTS.md`, `global/CLAUDE.md`, gate scripts, `rules/` | Mechanisms, contradictions, dangling references |

Limits: the 2026-10-09 run's `.claude/prd-flow/state/` is git-ignored and its transcripts are on the other machine, so the questions of that day are not visible; question evidence comes from the two local sessions. Almost all thinking blocks are empty (21 of 868), so misbehavior evidence is behavioral plus the chief's own audit.

## 2. Headline numbers
| Run | Numbers |
|---|---|
| 2026-10-09 clara-ai | 13:17 to 17:07 (about 3h50); 23 commits, 7 only lint and format; close phase about 2 h, 9 attempts, 2 passed; about 177 min of full-suite machine time, 74 of it in runs that then failed lint; about 130 min of agents blocked waiting; every full suite died at 40% while compare said "0 new failures" |
| f57d6438 (chief's audit) | 19 user interactions, 33 questions, 14 interactions before any code; about 2.06M subagent tokens in PRD and interview versus 1.72M for all code; 7 agents over the 150k ceiling |
| 9528886a | 13 AskUserQuestion calls; 132 doc edits, 35 on one `rules.md`; 24 min of day-1 work thrown away, 42 min to redo with 11 cold-start agents |
| voz-sempre-igual docs | 32 min of wall time for 71 s of tool time: the docs phase is bound by generated text, not by tools |
| f57d6438 (telemetry, section 9) | 46 subagents, 4,327 events; about 230 agent-minutes stuck on orphan shells (6 executors alive 14 to 56 min for 3 to 5 min of tool time); 53 heredoc commands; 39 to 55 min from the first survey to the first code line per slug, after 96 min of diagnosis chat |

## 3. Gates and close (from the pt-BR audit, confirmed)
| ID | Priority | Problem | Fix |
|---|---|---|---|
| G1 | P0 | Full suites die at 40% (`--timeout=90` kills the session through a gate test that runs `gates.sh full` with `timeout=300`; pytest-timeout on Windows calls `os._exit`); `gates.sh` drops the exit code with `|| true`; `new_failures.py` counts only `FAILED` lines, so "0 new failures" | Compare and baseline fail when pytest exits without its summary line; the gate test runs only on Linux CI or kills its tree under 90 s; rerun the real suite of the three slugs |
| G2 | P1 | Close runs the full suite before a 2 s lint (compare, lint, trailers, docs, retro); 7 of 9 closes failed lint after 10 to 18 min | Lint, trailers and docs first, compare last; the executor lints its own files before each commit (see B-a BA2) |
| G3 | P1 | Reuse is keyed by HEAD sha, so the C5 `docs(prd): promote` commit always invalidates it; no cache across slugs; about 13 full suites in one day | Key by a hash of the test-relevant content (`HEAD:src`, `HEAD:tests`, lockfiles, dirty diff); shared cache `state/_compare/<hash>`; a docs-only commit reuses |
| G4 | P1 | Agents blocked up to 600 s in foreground waits (11 calls of 580 to 591 s, 5,455 s); `timeout 580 tail -f | grep -m1` does not wake when the job ends; a killed close left a 0-byte log | Close never runs the suite inline; close writes its log per step; long commands in background, woken by the completion notice |
| G5 | P1 | Three slugs in one working tree: up to 3 suites at once, verify diffs the dirty tree and other slugs' commits, repo-wide lint blocks every slug for one slug's import | One slug per tree or a worktree per slug; verify on `ref..HEAD` crossed with Owns; close lint scoped to the slug's files; kit scripts excluded by pattern; the brake as a checked rule |
| G6 | P2 | WinError 206 in `related`: every changed path passed on the command line | `--args-file`, filter by `code_extensions` first |
| G7 | P2 | `related` picks `tests/integration` and breaks the offline guard | `tests.related_exclude` |
| G8 | P2 | `related` over its 60 s budget (uv startup, psycopg import, `test_architecture` in `tests.always`) | Fix G7, move `test_architecture` to compare, measure only pytest time |
| G9 | P2 | cp1252 encoding errors with piped stdout | `PYTHONUTF8=1` in `gates.sh`, `reconfigure` in `gate.py`, same env in the test |
| G10 | P2 | Suite slow by construction: always `--cov`, no xdist | `--no-cov` and `-n auto` in baseline and compare; coverage in CI |
| G11 | P2 | 4 to 6 processes per tool call from the telemetry hooks; `config_get.py` once per key | `commands.python` set, no probe; config resolved in one call |
| G12 | P2 | One global telemetry context file, last writer wins; every close printed "retro sara-calada"; no subagent, compaction or wait events | `retro --context <slug>`; context from `AI_KIT_CONTEXT` per dispatch |
| G13 | P3 | Executors broke rules: code before test, edits by `sed -i` and heredocs, a forbidden Co-Authored-By trailer | See sections 6 B-a and B-e: most of these are caused by the instructions |
| G14 | P3 | Docs rework and repeated reads: voz `rules.md` edited 16 times, `plan.md` 9; CHANGELOG (150 KB) and `voice.md` (60 KB) read whole; `repo.md` read 9 times by 7 agents | See sections 4 and 6 |
| G15 | P3 | 5 permission denials, each a user round trip | See section 6 B-e |

## 4. The docs and PRD phase
### 4.1 Causes, by impact
| ID | Cause | Evidence |
|---|---|---|
| D1 | Scope is confirmed last. Round 0 confirms the domain model (entities), never what changes and what stays | sara: "only change the voice, not the agents" arrived at the read-back after the rules were written; 24 min and 4 agents lost, 42 min to redo |
| D2 | A design decision nobody asked about enters the PRD. D11 asks "how does it go back **without a deploy**?", which presumes a switch; constitution II pushes toward configuration | voz: 37a55391 (14:50) wrote the env var `SPEECH_TO_SPEECH_FAREWELL_BY_REALTIME` as a "rollback without deploy"; the question surfaced only after TRD and plan existed; 0b7876db, f2c42eda, 5e1e5f4e (15:35, DEC-44 "keep it in code") rewrote about 8 files in 3 commits, 45 min later |
| D3 | Four agents author questions (surveyor, docs `rules` follow-ups, delta re-survey, docs `prd-plan` WF69) with no record of the topics already asked | sara "who writes the why": 4 times in 3 wordings; "do the rules describe what you want?": 5 times; f57d6438 "Conferência" and "Inferência": 3 times each; voz DEC-41 and DEC-43 decide the same scope twice and quote the same user sentence |
| D4 | A question the user does not understand is rephrased, never explained with today's rule (WS08 "cut by half", R07 "no IDs", the plain-words lint, CE12 budgets) | sara user: "I did not understand. What does the voice have to do with it? **How is this rule in the PRD today?**" |
| D5 | Five confirmation layers on the same content: change question, round 0, rounds, read-back "is it clear?", plan round with prose and read-back again | 14 of 19 user interactions before code (f57d6438) |
| D6 | The record is ceremony the gate checks: `rules.md` plus `delta.md`, rendered to `approved-rules.md`, `interview.md`, `decisions.md`, copied literally to the PRD, `Decisions:` in the CHANGELOG, copied again by promote | `rules.md` edited 35 and 25 times; the top gate failure is Q3 "no `Confirmed:` line" (7 times), then Q1 (pack row paraphrased) and G2 (INDEX behind, one rerun per batch of IDs); agents read `gate.py` source or ran `--help` before the first call; voz CHANGELOG ended with two `## voz-sempre-igual` sections; DEC rows pasted 3 times; each rule row written twice (marker, then promote) |
| D7 | A cold docs agent per round, rereading `repo.md`, references and a 32 KB `state.md`; DP03 allows resume but nothing makes it happen | the chief edited `state.md` about 52 times to flip `running` to `done`; 10 agents read `state.md` whole; rule cells of hundreds of characters (C-PER-06, C-PER-09) rewritten whole on each tweak |
| D8 | A tooling denial became a product question | `Read(./CHANGELOG.md)` deny in settings: asked twice, unresolved |

### 4.2 How the interview works today
| Step | Who | What the user sees |
|---|---|---|
| 1 | surveyor `full` | nothing: confrontation, 16 dimension states, scaffolds, every question round |
| 2 | chief | confrontation plus "change, keep or adjust?" |
| 3 | chief | round 0: the domain model in one sentence, confirm or correct (two corrections allowed, each a delta re-survey) |
| 4 | chief, then a new docs `rules` per round | rounds of at most 4 questions in AskUserQuestion; after each, `rules.md`, render, `gate.py --rules`, read-back, the next round plus follow-ups |
| 5 | chief | "is it clear?", repeated until the user says clear |
| 6 | docs `prd-plan` | wave table, prose and the read-back again; a TRD-only decision (WF69) goes back to the user after the PRD is written |

### 4.3 Loop mechanisms
| ID | Mechanism | Source |
|---|---|---|
| L1 | The question count follows a checklist (D01 to D15 plus repo extras), not the decisions; D08 and D13 "always get a real answer" | interview.md "Dimensions"; impact.md "Pre-interview states" |
| L2 | No cap on rounds ("repeat until the user says clear"); follow-ups after every round | SKILL.md C5 step 3; prd-flow-docs.md `rules` |
| L3 | Four question authors, no topic record | interview.md, DP05, docs Plan step 4 |
| L4 | Rephrase instead of explain | WS08, R07, impact.md "Language" |
| L5 | Scope never asked | WF67 |
| L6 | Mechanism decisions are not questions; D11 presumes a switch | interview.md D11; WF69 |
| L7 | Five confirmation layers | SKILL.md C5 steps 2 to 5 |
| L8 | Format ceremony checked by the gate | gate_interview.py Q3, state_record.py |

### 4.4 What the surveyor carries in `full` mode
Batch 1 (8 reads and commands, `ai-kit.json` of 58 KB read whole), the domain model, the functional proof F1 to F3 of every rule, the sweep K01 to K14 (a remote grep over 30 refs included), conflicts written in 3 places, protected rules, owner, 16 dimension states, `pack.md` with `gate.py --pack`, `gate.py --snapshot`, the fan-out decision, `rules.md` and `delta.md`, three rendered scaffolds (next free IDs, change number), `impact.md`, `## Survey` with the confrontation and every round in the question format (labels, `rule-text` marks, `[row:]` tags, a scenario-wrong option per question, plain words), `gate.py --questions`; all within about 40k tokens and 50 calls. The proof and the sweep are the value; the scaffolds and the question ceremony are the overload.

## 5. The 16 dimensions: what they actually buy
| Question | Finding |
|---|---|
| Only measured gain | Eval S7 (minimum order of 30.00): prd-flow 7 of 7 hidden tests versus 4 of 7 (LS24). The gap ("before or after the discount?") was found by the K11 and K14 sweep (the minimum crossing the discount rule), not by the table |
| Did the record keep the answers? | No. In the same S7 the D13 answer ("every order from now on, no flag, no migration") was lost because `interview.md` is deleted at close (AUDIT-v5 section 4), and DEC-03 "no new public name" never reached the executor, which created one |
| What the gate checks | Form: 16 rows present, allowed states, a `Confirmed:` line. It was the most frequent gate failure in real runs and never caught a product error |
| What it costs | Every `open` dimension is a question; D08 and D13 are mandatory even when nothing changes; D11 induced the voz env var |
| Does a PRD-writing model need it? | It already knows to think about failures, transitions and contracts. What it does not know comes from the repository: today's literal rule, the neighbor rules that conflict, what the code really does. That is the sweep and the proof |

Verdict: remove the table, the record and gate Q3. Keep one line in the surveyor file: "before writing the sheet, check failure paths, requests in flight during the deploy, consumers of the data, tenant variation and safety; ask only where a real alternative exists". Clinical safety (clara-ai D16) stays a protected rule under the constitution.

## 6. Instructions that make behavior worse
Same kind of problem as the dimensions: context an agent follows faithfully and that makes it slower or wrong.

### B-a. Prohibitions that block the obvious action
| ID | Instruction | What happened | Fix |
|---|---|---|---|
| BA1 | Chief card: "Forbidden: preparing a question" | Chief, in its own audit: "the skill forbids me to rewrite a question, so I could only pass it on"; one question asked 3 times | The chief may explain and rephrase with today's rule, and read the PRD rows the sheet cites |
| BA2 | Executor: "no related tests, suites, gates or lint runs" | 7 of 9 closes failed on lint; 7 lint-only commits | The executor formats and lints its own files before each commit |
| BA3 | "Move code by script, never retype", "no `python -` heredoc", "edit with Edit", no move tool shipped | 6 executors stuck 14 to 56 min on hung heredoc shells (over 4 h of agent time); one ran `taskkill /IM python.exe` | Ship `gates.sh move`; the rule applies only to C6 refactors |
| BA4 | DP01 "no domain assumption in a prompt"; surveyor reads only PRD and code | Recommendations contradicted a preference the user had stated; 2 corrections | Pass the user's stated preferences verbatim as `Preferences:` |

### B-b. Contradictions between files
| ID | Side A | Side B | Cost seen |
|---|---|---|---|
| BB1 | Agents: long commands foreground, timeout up to 600000 | global/CLAUDE.md:10,24, AGENTS.md:49, DP02: background | about 130 min of blocked agents (G4) |
| BB2 | reviewer.md:39, recheck.md:28: Medium goes pending | review.md V04, SKILL.md:55: Medium goes to a fix and counts a round | 3 extra user round trips, close run twice |
| BB3 | agent-plan.md:94 (copied into every plan): close runs the full suite | E18, E20, V09, DP07: the chief runs compare, close reuses it | Close ran the suite inline |
| BB4 | prd-writing.md:19, trd-planned.md:61, agent-plan.md:23: separate `gate.py --step` calls, 2 reruns | docs agent, DS46: one `gates.sh docs`, one rerun | Extra gate runs |
| BB5 | agent-plan.md:23: docs starts the baseline with `--bg` | DP06: only the chief, never `--bg` | Baselines inside docs agents (LS31) |
| BB6 | kit/CLAUDE.md:27, AGENTS.md:40: run related tests | Executor: only its own test; its Self-check demands "structure tests ran, green" | An executor cannot be honest and compliant at once |
| BB7 | C4 ends in executor close | Baseline starts only for C2, C3, C5, C6 | Every C4 close fails "baseline missing" |
| BB8 | Agents: 15 lines plus five fields | global and AGENTS.md: 20 lines Done/Files/Tests/Gaps | "return the five fields" re-dispatches |
| BB9 | Surveyor and docs `model: opus` | "sonnet by default, opus with a written reason" | Cost |

Root cause: the orchestration rules (review policy, verification, full suite, baseline) live in six places (SKILL.md, execution.md, review.md, agent-plan.md, the docs Plan step that pastes two paragraphs into `## Plan`, and every plan header), and they drifted.

### B-c. Ceremony without product value
| ID | Instruction | Fix |
|---|---|---|
| BC1 | Every doc written twice: PRD row with the pending marker then stripped; TRD Planned then merged into the body; DEC rows in three places; the plan header copying the execution rules | Write once: final PRD rows (the change folder says what is pending), no TRD Planned (the cards map the files), DEC only in decisions.md |
| BC2 | Executor Self-check of 7 lines (PII, soft-delete, tenant scope, key-off parity...) for every task | Only the lines the card's Lens or rules ask for |
| BC3 | Warnings the agent must ignore: G25 printed 111 times across 15 agents; G29 and G32 "run /docs-html" 20 times although prd-flow must not run it; G28 9 times; Q9 false positive on pt-BR (English-only regex) | A warning that needs no action is not printed |
| BC4 | Gate flags documented only in `gate.py` source | `gate.py --help` lists them; agent files name the exact command |
| BC5 | A one-row change is size M (brief plus plan, TRD, baseline, waves, review, promote) | A one-rule C5: sheet, PRD row, one card, close; brief only for size L |
| BC6 | E01: a fresh session is mandatory with more than 2 waves left | Only past about 120k tokens in the chief, as an offer |

### B-d. Unreadable or dead context
| ID | Instruction | Fix |
|---|---|---|
| BD1 | Rule IDs from `rules/` (TS45, SA51, WF72, LT01 to LT12, RV18...) cited in runtime files; `rules/` is not installed in projects, and LT and RV18 are not in the catalog | Runtime files cite only headings of files the agent loads |
| BD2 | "context 6 lines, round 25" (SKILL.md:16) defined nowhere; CE12 limits plus R07 plus the plain-words lint strip the context out of questions | Replaced by the decision sheet |
| BD3 | interview.md says step 4, SKILL.md step 3; E04 points to a line in dispatch.md; agent-plan.md:103 says executors get the plan path, E15 says they read it from `## Plan` | One home per rule |
| BD4 | Constitution numerals in kit/CLAUDE.md differ from the constitution template | Generate the index from the template |

### B-e. Clashes with the harness and the settings
| ID | Clash | Cost | Fix |
|---|---|---|---|
| BE1 | `settings.json` denies `Read(./CHANGELOG.md)`; the flow must write the CHANGELOG | 6 denied calls, 2 user questions, docs gate red over 1 h | Doctor and surveyor batch 1 check that the files the flow writes are readable and writable; a denial is never a product question |
| BE2 | Harness attribution reminder versus the project's no-trailer rule | One commit amended | The commit line says which trailer wins |
| BE3 | Harness: subagents return findings as text; the reviewer writes `findings-r<N>.md` | 2 blocked writes | Findings in the return; a file only past the line cap |
| BE4 | Chained commands mandated (`git add ... && git commit -F -`, format and commit) that the permission classifier blocks | 5 denials, each a user round trip | One command per call |

### B-f. Flow shapes that do not fit real work
| ID | Shape | Cost | Fix |
|---|---|---|---|
| BF1 | One slug per repository, no multi-repo change | 3 runs for 1 problem; confirmations tripled; a fourth surveyor (92 calls, 45 state edits) only to align names | One slug, one sheet, rows grouped by repository |
| BF2 | Survey before asking where the change lives | Survey in the wrong repo, slug closed, rules discarded next day | The repository is the first check, before any survey |
| BF3 | Three slugs in parallel in one working tree | G5 | The chief refuses a second slug in the same tree; a worktree per slug |

## 7. Proposal
### 7.1 One decision sheet, answered in the chat
| Step | Who | What |
|---|---|---|
| 1 | surveyor `full` | Proof and sweep as today; writes `pack.md` and `sheet.md`, nothing else |
| 2 | chief | Prints `sheet.md` as its message and ends the turn. No AskUserQuestion, no round 0, no separate change question |
| 3 | user | Types the answer: `ok` accepts every recommendation and assumption, or `1B, 3A, A2: <correction>, scope: <correction>` |
| 4 | docs `apply`, one dispatch | Writes `answers.md` (the message verbatim), the record, PRD, TRD and plan; an unclear answer or a new decision: one follow-up sheet with only those items |
| 5 | chief | Prints the rule diff as written (today, then new) plus the wave table; one approval; a correction is an in-place `adjust` |

At most 2 user touchpoints before code (3 with the one follow-up), against 6 to 13 today. An item still open after the follow-up becomes a `Q-` row with the recommended default, visibly open.

Sheet blocks, in order: **what changes in the rules** (rule, today literal, new text, rewrites, adds or supersedes), **what does not change** (mandatory scope), **assumed** (at most 8 lines), **decisions** (at most 8, numbered). Each decision, illustrative from the voz case:

> **2. How to undo the new farewell if it misbehaves** · rule C-DSP-02
> **Today:** the farewell is spoken by the regular speech synthesis; changing it needs a deploy.
> **What changes:** the farewell is generated by the realtime voice model.
> **Why decide now:** if the new voice fails in production, this sets how long patients hear the wrong farewell.
> - **A) Roll back with a deploy (Recommended):** nothing new to configure; undoing takes a deploy.
> - **B) A configuration switch:** undone at once; one more setting to keep and test both ways.
>
> **Example:** the new voice cuts off on a Friday night: with A it returns on the next deploy, with B in minutes.

| Behavior rule | Fixes |
|---|---|
| Every decision shows Today (with the rule ID), What changes, Why decide now, options with consequences, the recommended one and an example | D4 |
| A rollback, switch, configuration key, environment variable, table or endpoint is always a sheet decision; docs never adds a mechanism on its own; the gate flags a new one without a DEC row | D2 |
| One decision per rule and scope; the lint flags two items on the same topic | D3 |
| Not understood: answer with today's rule and an example; never the same question in new words | D4 |
| At most 8 decisions; more means split the change | readability |
| One follow-up; then `Q-` rows | L2 |
| One final approval: the diff as written plus the wave table | D5 |

### 7.2 Less ceremony per agent
| Agent | Keeps | Drops |
|---|---|---|
| surveyor | proof, sweep, `pack.md`, `sheet.md` | three rendered scaffolds, dimension table, `[row:]` tags, `rule-text` marks, per-question scenario-wrong option, reading `ai-kit.json` whole |
| docs | one `apply` dispatch, `adjust` | per-round `rules`, folded mode, hand-written `Confirmed:`, the `rules.md` to `delta.md` to render chain |
| chief | prints the sheet, passes the reply verbatim, dispatches, may explain a question | folded-or-not decisions, ledger edit per return |
| gate | content: every touched rule in the diff, every decision answered, no mechanism without a DEC | Q3 (form), Q6 to Q9 |

Also: DEC rows only in `decisions.md`, read by executor and reviewer; promote writes one CHANGELOG entry per slug.

### 7.3 Meta-rules for writing kit instructions (MAINTAINING.md)
| ID | Rule | Check |
|---|---|---|
| M08 | Never forbid without naming the allowed way that works on Windows, macOS and Linux | Review of every "never" line |
| M09 | A gate checks product content; a form-only error or a warning that needs no action is removed | Gate codes per run in the eval |
| M10 | One home per rule; other runtime files link by heading | Test: same sentence, or same number with different values, in two runtime files |
| M11 | Runtime files cite only what the agent can open | Test: every cited ID or heading resolves inside the installed files |
| M12 | Every instruction is checked against the harness (system reminders, settings deny, permission prompts) | `/ai-kit doctor` |
| M13 | At most 3 reference files before an agent's first action | Test on the agent files |

### 7.4 Workstreams and order
| Wave | Items | Content |
|---|---|---|
| 1 | I1, I5 | Sheet format, interview.md rewritten to about a third, gate checks `sheet.md` against `answers.md`, new lint |
| 2 | I2 to I4, B1 | Surveyor, chief and docs on the sheet; one home per orchestration rule, BB1 to BB9, BD1 to BD3 |
| 3 | B2, B3, B4 in parallel | Prohibitions with a working way (`gates.sh fix-files`, `gates.sh move`); ceremony out (BC1 to BC6); harness and shape (BE1 to BE4, BF1 to BF3, doctor) |
| 3 | I6 to I8 | promote single entry, rule rows and lesson LS32, eval |
| Parallel track | G1 to G12 | Gates and close; G1 first |
| 4 | Eval round | Before replicating to the three repositories |

### 7.5 Measuring it (M07)
The eval hands every decision in one block (`eval/prompt-phase2.md`), so it never had a question round. Add:

| Item | What |
|---|---|
| Metrics | `user_touchpoints`, `repeated_topics`, `post_prd_reversals`, `sheet_decisions`, gate reruns in the docs phase |
| Scenario S12 | The decisions file answers the sheet by number and leaves one answer ambiguous: checks the single follow-up and the `Q-` fallback |
| Adoption | The existing rule: quality metrics not worse, cost and time within the band |

| Target on the next real C5 | Today | Target |
|---|---|---|
| User touchpoints before code | 6 to 13 | at most 2 (3 with a follow-up) |
| Repeated topics | 3 to 4 | 0 |
| Decisions reversed after the PRD commit | 1 | 0 |
| `rules.md` edits | 25 to 35 | at most 2 per rule row |
| Gate failures in the docs phase | 5 to 7 | at most 1 |
| Closes failing on lint | 7 of 9 | 0 |

### 7.6 Risks
| Risk | Mitigation |
|---|---|
| A free-text answer is misread | The approval shows the diff as written; a correction is an in-place `adjust` |
| A long sheet is hard to read | Diff first, at most 8 decisions each with a recommendation, `ok` accepts all |
| The user stops halfway | Nothing is written until the answer; unanswered items take defaults only on `ok` |
| B3 changes document formats (PRD markers, TRD Planned) that promote and the gates read | B3 can ship as a second delivery |
| Repositories on the old format | `/ai-kit update`; a state folder from an old run finishes on the old route |

## 8. Open items
| Item | Owner |
|---|---|
| Decisions Q1 to Q6 of the plan (answer channel, cap of 8, one follow-up, dimensions removed, branch, track B in the same branch) | user |
| `sara-calada` close failed and the state is still open on the other machine | whoever ran it |
| Rerun the real full suite of the three slugs after G1 | after G1 |
| `fala-duplicada`: confirm the backend accepts the "leitura" origin (CS-003) | backend |
| Telemetry has no gate output, question text or AskUserQuestion wait; that is why this audit needed transcripts | G12, W5.3 of `plan-run-speed.md` |
| The 2026-10-09 transcripts and state folder, to confirm its questions | the person who ran it |
| Plan decision "dimensions removed": answered yes by the user on 2026-10-09 (section 9.1) | done |
| Orphan agents: P0 with a zero target (section 9.3), ahead of wave 1 | kit |

## 9. Addendum: session f57d6438 (orphans, late discoveries, context), from telemetry

Source: `.ai-kit/runs/*/events.jsonl` of clara-ai and agora-consulta-fe filtered on `sid=f57d6438` (4,327 events, 14:21 to 17:53 local), the 46 subagent returns, and the process table of the machine at 17:40 and 17:55. Runs: `voice-resilience` (clara-ai, C5 L), `assessment-inference` (clara-ai, C5 M), `conversation-reconnect` (agora-consulta-fe, C5 L). Outcome: front PR agora-consulta/fe-agoraconsulta#238, clara-ai PR agora-consulta/clara-ai#150 (draft).

### 9.1 User direction (Matheus, 2026-10-09)
> "Precisamos melhorar principalmente o PRD, a entrevista está travada, não precisamos de todas aquelas regras, 16 dimensões, isso tá trazendo ineficiência. Vamos limpar estas sujeiras de contexto e manter o contexto suficiente do agente. Se atentar com agentes órfãos igual aconteceu aqui de ficarem rodando por 50 minutos, isso não pode acontecer."

| Consequence | Where |
|---|---|
| The dimension table, its record and gate Q3 go (section 5 verdict confirmed) | 7.2, wave 1 |
| Every agent gets the smallest context that lets it do its job (9.5) | 7.2, M13 |
| Orphan agents are a P0 with a target of zero, before any interview work | 9.3 |

### 9.2 Orphan agents: evidence
| Agent (role, task) | Alive | Tool time | Longest call | Stuck |
|---|---|---|---|---|
| a8e59ca6 (executor, inference T03) | 56.0 min | 5.2 min | 120 s | 50.8 min |
| a2d37937 (executor, front T02) | 51.8 min | 2.9 min | 120 s | 48.9 min |
| ad3b05ea (executor, front T03) | 49.6 min | 2.8 min | 121 s | 46.8 min |
| ad256638 (executor, resilience T01) | 49.5 min | 2.9 min | 120 s | 46.6 min |
| a6da3d38 (executor, resilience T05) | 30.8 min | 4.9 min | 121 s | 25.9 min |
| a06754a2 (executor, resilience T07) | 14.0 min | 3.1 min | 120 s | 10.9 min |
| Total | | | | about 230 min |

Mechanism, in order:
1. The agent runs a Bash command whose heredoc delimiter never matches, so the child waits on stdin.
2. The Bash tool returns at its 120 s default timeout (every "longest call" above is 120 or 121 s); the child keeps running.
3. The agent finishes its task and returns, and the harness notes "stopped with background work of its own still running".
4. The harness counts the agent as alive until the orphan dies. SubagentStop for all six fired at 17:42, the minute the chief killed the processes.

Patterns found in the process table (all from subagents of this session):

| Pattern | Seen in |
|---|---|
| `python - <<'E' 2>/dev/null \|\| /c/Python314/python - <<'E2'` (fallback chain, delimiters never on their own line) | inference T03, resilience T07 fix, red-log tail |
| `cat >> tests/...py <<'EOF'` inside the shell snapshot's `eval '...'` quoting | resilience T01, T05, front T03 |
| `taskkill /IM python.exe` to clean up its own strays (kills every Python on the machine, other sessions included) | inference T02 |

Heredoc commands in the telemetry: 53 (45 executors, 5 docs, 2 surveyors, 1 reviewer), against a written rule that forbids them.

Why nothing stopped it:

| ID | Cause | Evidence |
|---|---|---|
| OR1 | The rule is text only. The single `PreToolUse` hook in `settings.json` is telemetry: it records the heredoc and never blocks | 53 recorded, 0 blocked |
| OR2 | No reaping. The chief card has no step for "background work still running"; the chief ignored the notice 6 times | Notices on a2d37937, a8e59ca6, a6da3d38, a06754a2, ad3b05ea, a96f68b8 |
| OR3 | Self-report is trusted. The last fix agent returned "No process left running" with a `python -` orphan alive since 17:41 | Process table at 17:55 |
| OR4 | Interpreter ambiguity invites fallback chains. `repo.md` says `python`, the dispatch prompt says `/c/Python314/python`, `.venv` holds the project Python, and `/c/Python314/python` cannot import `conftest.py` (no psycopg) | The `python - ... \|\| /c/Python314/python -` chains; a reviewer could not run pytest |
| OR5 | Killing an orphan can still write. Two hung `cat >>` processes appended duplicate tests into the tree when stopped | `test_reason_table_of_a_ws_08` and `test_failed_delivery_closes_undelivered` defined twice, uncommitted, discarded by hand |
| OR6 | The cleanup itself raced a new run: the chief stopped processes by pattern in the same message that started a new verify, and killed 3 processes of the new run | 17:45 |

### 9.3 Orphans: required fixes (P0)
| ID | Fix | Check |
|---|---|---|
| O1 | A blocking `PreToolUse` hook on Bash and PowerShell for `prd-flow-*` agents: deny `<<`, `python -` and any stdin-reading interpreter call, `cat >`, `cat >>`, `tee`, `taskkill`, `Stop-Process -Name`, `git checkout`, `git stash`, `git reset`, `git restore`; the deny message names the allowed way (Edit and Write, `gates.sh move`), per M08 | Kit test feeds the hook the patterns of 9.2 and the allowed equivalents |
| O2 | `gates.sh reap [--older-than N]`: lists python, node, bash, uv and pytest processes whose command line carries this session's shell snapshot id and whose parent agent ended, and kills the tree; never by image name | Kit test with a fake process list |
| O3 | Chief card, one line: a return or notice saying background work is still running is answered with TaskStop and `gates.sh reap` before anything else; `reap` also runs at every wave end and in close | `orphans_at_wave_end` = 0 in the eval |
| O4 | A watchdog in the telemetry hook: an agent alive past 30 min, or with no tool call for 10 min, is reported to the chief and reaped | Telemetry event `agent_stuck` |
| O5 | One interpreter. `ai-kit.json` `commands.python` (the project one, `.venv` or `uv run`) is the only interpreter any file or prompt names; no fallback chains | M10 test: one interpreter string across runtime files |
| O6 | The reaper, not the agent, certifies "no process left"; the Self-check line is removed | BC2 |
| O7 | Cleanup never runs in the same message that starts a suite; `reap` first, then the suite | Chief card |

Targets: `stuck_minutes` (alive minus tool time) = 0, `orphans_at_wave_end` = 0, heredoc calls = 0.

### 9.4 Interview: what this session adds
| ID | Finding | Evidence | Fix |
|---|---|---|---|
| IA | Decisions made in the conversation were asked again | 96 min of diagnosis chat before `/prd-flow`; the chief listed the same 4 numeric decisions (resume ceiling, checkpoint limit, sweep interval, patient message) in 3 chat messages, then the survey asked them again as Q1, Q6, Q7 | The chief passes `Decided in conversation:` verbatim; the surveyor turns each into an assumed line, never a question |
| IB | Recommendations went against what the user had said | Q2 recommended keeping a code check against the stored feedback "agents decide, code only transports"; Q3 recommended that an onset carries to a symptom told later, and the user corrected it at the read-back with a counter-example | BA4, plus: a recommendation cites the user's stated principle it follows, or says "no stated preference" |
| IC | Interacting answers were found only after the round | Q1 (an error retries alone) against Q6 (3 failed saves end the session by the error exit): docs found the conflict and asked Q6b | The sheet lists the interactions between its decisions; docs checks combinations before writing |
| ID | A numeric rule was approved without its number | "a high pain score answers yes" approved with no cutoff; the reviewer found it at the last wave (score 7) and it became a question mid-execution | Lint: a rule that depends on a number or a category names it in the sheet |
| IE | A "Checked" claim was not checked | The survey wrote "rollback by configuration, no migration (constitution II)" without reading the DB CHECK constraints; executor T01 found that `FAILED_RECORD` needs a migration; it cost a short survey, a question, docs, an ADR amendment and a fix (about 25 min, 3 agents) | A new state or enum value requires reading the constraints and migrations; every "Checked" line cites the file read |
| IF | A cross-repo contract was invented twice | Two surveyors named the same close reasons differently (`SESSION_FAILED` with a button against `SESSION_ENDED_UNRECOVERABLE`); an alignment surveyor took 12.5 min, 92 calls, 164k tokens | BF1: one slug, one sheet, the contract written once |
| IG | Preflight gaps became user interruptions after the plan | CHANGELOG deny (BE1, asked twice, still open); `jsdom` declared but not installed (the first front baseline exited 1 with no output, the rerun said 0 failures); change number 004 taken by two parallel slugs; the pre-existing `tsc` error found at close | Surveyor batch 1 or doctor: files the flow writes are writable, `gates.sh setup` is current, the change number is reserved atomically, lint and `tsc` are green on the base |
| IH | A question in code language asked 3 times | "Conferência" (copy of Sara's question): the user answered "O agente tem autonomia para responder isso de acordo com contexto. Porque conferir em código?" | BA1, D4 |

User touchpoints in this session: 19 AskUserQuestion calls, 33 questions; 12 of them in the 28 min between the end of the surveys (16:08) and the first executor (16:36). The time the user spent answering is not measurable: AskUserQuestion carries `ms=0` in the telemetry (section 8).

### 9.5 Context per agent: what to keep, what to drop
Tokens per agent in this session (from the subagent returns):

| Role | Agents | Tokens | Note |
|---|---|---|---|
| surveyor `full` | 3 | 157.7k, 175.8k, 191.5k | all over the 150k ceiling |
| surveyor delta (contract alignment) | 1 | 164.5k | only to reconcile two surveys |
| surveyor `short` (migration) | 1 | 114.7k | |
| docs `rules` and `prd-plan` | 3 | 157.1k, 169.8k, 185.7k | over the ceiling |
| docs contexts, ADR, adjust | 7 | 68k to 123k | |
| executors | 23 | 30k to 147k | |
| reviewers and recheck | 8 | 32k to 69k | |
| Phase totals | | about 2.06M interview and docs, 1.72M code, 0.38M review | the interview cost more than the code |

| Keep (sufficient context) | Drop (context debt) |
|---|---|
| The literal text of every rule row the change touches, and its neighbors that conflict | The 16-dimension table, its states and gate Q3 |
| Code proof as `file::symbol` | The three rendered scaffolds and the `rules.md` to `delta.md` to render chain |
| The user's decisions and preferences, verbatim | `[row:]` tags, `rule-text` marks, a scenario-wrong option per question |
| The cross-repo contract, written once | Kit rule IDs the agent cannot open (SA51, WF72, DP01) |
| The card: Owns, the test to write, the rows it serves | The plan header copy of the orchestration rules; gate warnings that need no action |
| | Whole reads of `ai-kit.json`, `state.md`, `CHANGELOG.md`, `voice.md` |

Targets: surveyor at most 60k tokens, docs `apply` at most 80k, no agent over 150k, interview tokens below code tokens.

### 9.6 Orchestrator findings
| ID | Finding | Fix |
|---|---|---|
| CH1 | Ignored 6 "background work still running" notices | O3 |
| CH2 | Ran two slugs in the same clara-ai tree in parallel: one slug's verify picked up the other's failures; the shared `_tests/related.log` and `red.log` were overwritten; compare had to be held | G5, BF3, a log file per slug |
| CH3 | `gates.sh verify` prints the slowest tests, not the failures, so the chief opened logs against its own card | Verify prints the FAILED ids and the first assertion line of each |
| CH4 | Relayed agent claims without checking (no process left, tests run) | O6; the reviewer reads the verify output, not the Self-check |
| CH5 | Opened 3 slugs for one user problem | BF1 |
| CH6 | Started a cleanup in the same message as a new suite | O7 |

### 9.7 Metrics to add (M07)
| Metric | This session | Target |
|---|---|---|
| `stuck_minutes` (alive minus tool time, summed) | about 230 | 0 |
| `orphans_at_wave_end` | 6 at 17:40, 1 more at 17:55 | 0 |
| Heredoc commands | 53 | 0 |
| User touchpoints before code | 14 | at most 2 (3 with a follow-up) |
| Questions after the plan was approved | 5 (jsdom, score cutoff, migration, CHANGELOG, `tsc` and hold) | 0 |
| Interview and docs tokens / code tokens | 2.06M / 1.72M | below 1 |
| Agents over 150k tokens | 7 | 0 |

### 9.8 Open items from this session
| Item | Owner |
|---|---|
| clara-ai#150 out of draft: on `4302506b` the related tests are green, but both compares printed `+++ Timeout +++` and then "new failures: 0 (baseline: 1)", so G1 reproduced in this session and the full suite is unproven; CHANGELOG entries still blocked (the user declined removing the deny line from `settings.json`); real-model eval of `registro-da-conversa/05..12`; integration test of the sweep in nonprod | user and chief |
| clara-ai Lows CS-R3-03 (a connected row of a dead replica is swept only at boot) and CS-R3-05 (900 s alert grace is a literal) | user decision |
| fe#238 ships with clara-ai#150; then promote CNX-04, CNX-05, CNX-08 and archive `changes/003-conversation-reconnect` | chief |
| A bash process of another session (shell snapshot of 2026-10-08 14:17) is still alive on this machine; not touched | user |

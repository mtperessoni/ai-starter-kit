# Plan: one-pass interview (lessons of the voz, sara and assessment runs, 2026-10-08/09)

Status: proposal, waiting for approval; Q4 (dimensions removed) decided by the user on 2026-10-09; workstream O (orphan agents, P0) and items I9 to I11 added from `eval/AUDIT-prd-flow-run-2026-10-09.md` section 9. Source: clara-ai runs `voz-sempre-igual` (origin/staging a1f1216a..b6f46280), `sara-welcoming-tone` and the three-slug session (voice-resilience, assessment-inference, conversation-reconnect). Evidence files: `git-docs-phase.md` and `telemetry-docs-phase.md` (scratchpad of session 5dcb60e5).

## Why
| Evidence | Value |
|---|---|
| Questions to the user | sara 13 AskUserQuestion calls; three-slug session 19 calls (38 questions) plus 4 plain-text rounds |
| Same topic asked again | sara "who writes the why": 4 times in 3 wordings, then the user: "I did not understand. How is this rule in the PRD today?"; "do the rules describe what you want?": 5 times; "Conferência" and "Inferência": 3 times each; voz DEC-41 and DEC-43 decide the same scope twice |
| Scope found last | sara: "only change the voice, not the agents" arrived at the read-back, after the rules were written: 24 min and 4 agents thrown away, 42 min to redo |
| Decision invented, then reversed | voz: an env var rollback switch written into the PRD at 14:50 that nobody asked about; reversed at 15:35 (DEC-44) across about 8 files and 3 commits |
| Record churn | `rules.md` edited 35 times (sara) and 25 times (two slugs); the most common gate failure is Q3 "no `Confirmed:` line" (7 times) |
| Blind spot of the eval | `eval/prompt-phase2.md` hands every decision in one block, so no eval run ever had a question round (0 questions in 19 eval transcripts). The interview cost was never measured |

## How the interview works today
| Step | Who | What the user sees |
|---|---|---|
| 1 | surveyor `full` | nothing; it writes the confrontation, 16 dimension states, scaffolds and every question round |
| 2 | chief | confrontation plus "change, keep or adjust?" |
| 3 | chief | round 0: the domain model in one sentence, confirm or correct (two corrections allowed, each a delta re-survey) |
| 4 | chief, then docs `rules` | rounds of at most 4 questions in AskUserQuestion; after each round a new docs dispatch writes `rules.md`, renders, runs `gate.py --rules`, returns a read-back and the next round, plus follow-ups for any answer "that does not decide its row" |
| 5 | chief | "is it clear?" read-back, repeated until the user says clear |
| 6 | docs `prd-plan` | wave table, prose and (folded) the read-back again; a TRD-only decision found here (WF69) goes back to the user after the PRD is written |

### Where the loops come from
| ID | Mechanism | Source |
|---|---|---|
| L1 | The question count follows a checklist (D01 to D15 plus the repo's extras), not the decisions: every `open` dimension is a question, D08 and D13 "always get a real answer" | interview.md "Dimensions", impact.md "Pre-interview states" |
| L2 | No cap on rounds: "repeat until the user says clear"; docs `rules` adds follow-ups after every round | SKILL.md C5 step 3; prd-flow-docs.md `rules` |
| L3 | Four authors of questions (surveyor, docs `rules`, delta re-survey, docs `prd-plan` WF69) and no record of the topics already asked | interview.md, dispatch.md DP05, prd-flow-docs.md Plan step 4 |
| L4 | A question that is not understood is rephrased ("restart from the example and cut by half"), never answered with today's rule, because questions may not show IDs or the current text | WS08, R07, impact.md "Language" |
| L5 | Scope is never asked: round 0 confirms the entities, not what changes and what stays | WF67 |
| L6 | Mechanism decisions (rollback, switch, config or code) are not questions; D11 asks "how does it go back **without a deploy**?", which presumes a switch | interview.md D11; WF69 finds them after the PRD |
| L7 | Five confirmation layers on the same content (change question, round 0, rounds, read-back, plan round) | SKILL.md C5 steps 2 to 5 |
| L8 | The record is ceremony the gate checks: a 16-row Dimensions table, a hand-written `Confirmed:` line per table, rendered files from `rules.md` and `delta.md` | gate_interview.py Q3, state_record.py |

### What the surveyor carries in `full` mode
Batch 1 (8 reads and commands, `ai-kit.json` of 58 KB read whole), the domain model, the functional proof F1 to F3 of every rule, the sweep K01 to K14 (a remote grep over 30 refs included), conflicts written in 3 places, protected rules, owner, 16 dimension states, `pack.md` with `gate.py --pack`, `gate.py --snapshot`, the fan-out decision, `rules.md` and `delta.md`, three rendered scaffolds (next free IDs, change number), `impact.md`, `## Survey` with the confrontation and every round in the question format (labels, `rule-text` marks, `[row:]` tags, a scenario-wrong option per question, plain words), `gate.py --questions`, within 40k tokens and 50 calls. The sweep and the proof are the value; the scaffolds and the question ceremony are what overload it.

## Target design: one decision sheet, answered in the chat
| Step | Who | What |
|---|---|---|
| 1 | surveyor `full` | Proof and sweep as today. Writes `pack.md` and **`sheet.md`**, nothing else in the state folder |
| 2 | chief | Prints `sheet.md` as its message and ends the turn. No AskUserQuestion, no round 0, no separate change question |
| 3 | user | Answers in the prompt: `ok` accepts every recommendation and assumption, or `1B, 3A, A2: <correction>, scope: <correction>` |
| 4 | docs `apply` (one dispatch) | Writes `answers.md` (the user's message verbatim), the record, PRD, TRD and plan. An answer that is unclear or opens a new decision: one follow-up sheet with only those items, then stop |
| 5 | chief | Prints the rule diff as written (today, then new) plus the wave table; one approval. A correction is an in-place `adjust` |

At most 2 user touchpoints before code (3 with the one follow-up). After the follow-up, an item still open becomes a `Q-` row with the recommended default, visibly open (what S7 grades).

### Format of `sheet.md` (illustrative; prose in the `repo.md` language)
```markdown
# <the change in one line>

## What changes in the rules
| Rule | Today (literal) | Becomes | Kind |
|---|---|---|---|
| CHK-02 | "Payment waits 30 s for the provider" | "Payment waits 20 s, then shows try again and keeps the cart" | rewrites |
| CHK-13 | (none) | "A payment in flight during the deploy keeps its timeout" | adds |
| CHK-07 | "Shows a spinner until the provider answers" | (removed, CHK-02 covers it) | supersedes |

## What does not change
- Shipping, discounts and the receipt layout.

## Assumed (holds unless you correct it)
- A1 Applies to every tenant (shared config).
- A2 Rollback: a deploy of the previous version.

## Decisions (answer by number)
**1. When the provider is slow** · rule CHK-02
Today: the customer waits 30 s, then sees an error and the cart is lost.
Why it matters: about 4% of payments take more than 20 s.
- A) 20 s, then "try again", cart kept (Recommended): fewer stuck carts; a slow success may be charged twice on retry
- B) 60 s: fewer false failures; the customer waits longer
Example: provider answers at 45 s, then (A) shows "try again" with the cart intact.

## How to answer
`ok` accepts every recommendation and assumption. Otherwise: `1B`, `A2: <correction>`, `scope: <correction>`. If a scenario is wrong, say its number.
```

| Sheet rule | Detail |
|---|---|
| Diff first | Every rule the change touches is a row with the literal text of today and the new text; conflicts found by K01, K11 and K14 are rows of this table (`rewrites` or `supersedes`), not a separate question |
| Scope | "What does not change" is mandatory: it is what sara's user corrected at the end |
| Assumed | Defaults the change relies on, one line each, at most 8. The 16 dimensions are removed (table, record and gate Q3): their only measured gain (S7, 7 of 7) came from the K11 and K14 sweep, and the D13 answer was lost anyway because `interview.md` is deleted at close. In their place, one line in the surveyor file: "before writing the sheet, check failure paths, requests in flight during the deploy, consumers of the data, tenant variation and safety; ask only where a real alternative exists" |
| Decisions | Only real alternatives; at most 8. More than 8 means the change is too big: the sheet recommends splitting it |
| Mechanism | A rollback, switch, configuration key, environment variable, table or endpoint that the change needs is a decision of the sheet, never something the docs agent adds |
| Context | Each decision has `Today:` (the current behavior, with its rule ID), why it matters and an example; IDs are allowed in context lines |
| Protected and owner | Decision items of the sheet, first |
| One topic, one item | Two items never decide the same rule and scope; the lint checks it |

## What changes in the kit
| Today | New | Rules |
|---|---|---|
| Rounds of 4 in AskUserQuestion, repeated until clear | One sheet in the chat, one follow-up at most | CE12, CE27, WF14, WF15 (amend) |
| Round 0 domain model | The sheet's title, diff and "What does not change" | WF67 (replace) |
| Change question (change, keep, adjust) | Answering the sheet; "keep today's rule" is an option of decision 1 when relevant | WF10 (amend) |
| 16-row Dimensions record, `Confirmed:` per table, gate Q3 | `answers.md` verbatim; gate checks every sheet item has an answer or an adopted default | WF42, WF43 (replace) |
| Question lint Q6 to Q9 (row tag, scenario-wrong option per question) | Lint S1 to S4: each decision has Today, options and a recommended one; each touched rule is in the diff; no two items share a rule and scope; no jargon | WF68 (replace) |
| Rephrase when not understood | Show today's rule and an example; never the same question in new words | WS08 (amend), R07 (IDs allowed in context) |
| TRD-only decision found by the plan (WF69) | Mechanism decisions are surveyed and asked in the sheet; the plan finding one is a surveyor miss, routed as the one follow-up | WF69 (amend) |
| D11 "how does it go back without a deploy?" | "How does it go back: a deploy, a configuration, something else?" | interview.md D11 |
| docs modes `rules`, `prd-plan`, folded path | docs `apply` (one dispatch) and `adjust` | prd-flow-docs.md |
| Surveyor writes `rules.md`, `delta.md` and three rendered scaffolds | Surveyor writes `pack.md` and `sheet.md`; docs `apply` writes the record | prd-flow-surveyor.md, CE29 (amend) |
| Batch 1 reads `ai-kit.json` whole | Grep the keys it needs | prd-flow-surveyor.md |
| DEC rows pasted into decisions.md, the CHANGELOG draft and the promote entry | Written once in decisions.md; promote copies once; fix the duplicated `## <slug>` CHANGELOG section | WF47, promote.py |

## Workstreams
| Item | Change | Files | Test |
|---|---|---|---|
| I1 | Sheet format and rules; dimensions removed (one blind-spot line); `interview.md` reduced to the sheet | `reference/interview.md` (rewrite to about a third), `reference/impact.md` "Prepared questions", "Pre-interview states" | |
| I2 | Surveyor `full` writes only `pack.md` and `sheet.md`; batch 1 lighter | `agents/prd-flow-surveyor.md` | |
| I3 | Chief: print the sheet, end the turn, pass the reply verbatim; one follow-up; one approval | `SKILL.md` C5 route and Returns, `reference/dispatch.md` task lines | |
| I4 | Docs `apply` and `adjust`; never add a mechanism outside the sheet or the answers | `agents/prd-flow-docs.md` | |
| I5 | Gate: Q3 checks `sheet.md` against `answers.md`; new lint S1 to S4 replaces Q6 to Q9; `state_record.py` renders from the answers | `gate_interview.py`, `state_record.py`, `gate.py --rules` | `tests/test_gate_questions_state.py`, `test_gate_rules_v4.py`, `test_state_record.py` |
| I6 | promote writes one CHANGELOG entry per slug | `promote.py` | `tests/test_promote.py`: second promote of the same slug |
| I7 | Rule rows and lesson | `rules/07-workflow.md`, `01-context-economy.md`, `08-writing-style.md`, `09-lessons.md` (LS32), `CHANGELOG.md` | |
| I8 | Eval that sees the interview: metrics `user_touchpoints`, `repeated_topics`, `post_prd_reversals`, `sheet_decisions`; scenario S12 where the decisions file answers the sheet by number and leaves one answer ambiguous (checks the single follow-up and the `Q-` fallback) | `eval/run.py`, `eval/METRICS.md`, `eval/scenarios/S12` | |
| I9 | Answers already given: the chief passes `Decided in conversation:` (the user's verbatim words) and `Preferences:` (the feedback memories) to the surveyor; each becomes an assumed line, never a sheet decision; a recommendation cites the stated principle it follows or says "no stated preference" (audit IA, IB, BA4) | `SKILL.md` C5 step 1, `reference/dispatch.md` surveyor task line, `agents/prd-flow-surveyor.md` | eval: a decisions file that pre-answers 2 items yields a sheet without them |
| I10 | Preflight in surveyor batch 1 (and `/ai-kit doctor`): every file the flow writes is readable and writable under the settings; `gates.sh setup` current; lint and type check green on the base; a new state, enum or column value requires reading the DB constraints and migrations; the change number is reserved atomically across parallel slugs; every "Checked" line cites the file read (audit IE, IG, BE1) | `agents/prd-flow-surveyor.md`, `installer/ai-kit` doctor, `kit/scripts/next_change_number` | unit tests for the reservation and the settings check |
| I11 | Sheet lint, two more checks: S5 a rule that depends on a number or a category names it (audit ID, the pain-score cutoff); S6 the sheet lists the interactions between its decisions and docs `apply` checks the combination of the answers before writing (audit IC, Q1 against Q6) | `gate_interview.py`, `agents/prd-flow-docs.md` | `tests/test_gate_questions_state.py` |

| O | Orphan agents (P0, audit 9.2 and 9.3): O1 a blocking `PreToolUse` hook for `prd-flow-*` agents on Bash and PowerShell (deny heredocs, `python -` and stdin-reading interpreters, `cat >`, `tee`, `taskkill`, `Stop-Process -Name`, `git checkout`, `stash`, `reset`, `restore`; the message names the allowed way); O2 `gates.sh reap` kills the process tree of an ended agent by its shell snapshot id, never by image name; O3 the chief answers "background work still running" with TaskStop and `reap`, and runs `reap` at every wave end and in close; O4 a watchdog in the telemetry hook reports and reaps an agent alive past 30 min or idle 10 min; O5 one interpreter (`ai-kit.json` `commands.python`) named everywhere, no fallback chains; O6 the reaper certifies "no process left", the Self-check line goes; O7 never a cleanup in the same message that starts a suite | `kit/.claude/settings.json` hooks, `kit/scripts/guard_hook.py` (new), `kit/scripts/gates.sh` (`reap`), `kit/scripts/telemetry_hook.py`, `SKILL.md` chief card, executor and docs agents | `tests/test_guard_hook.py` (the 9.2 patterns denied, Edit and Write allowed), `tests/test_reap.py` (fake process list), eval metric `orphans_at_wave_end` |

Context budgets (audit 9.5), checked by the eval on every agent return: surveyor at most 60k tokens, docs `apply` at most 80k, no agent over 150k, interview and docs tokens below code tokens. What an agent keeps and drops is listed in audit 9.5 and is the acceptance list of I2, I4 and B3.

| B1 | One home per orchestration rule; fix BB1 to BB9 and BD1 to BD3; drop the pasted `Execution:` paragraphs and the plan header copy | `SKILL.md`, `reference/*.md`, agent files, `kit/CLAUDE.md`, `kit/AGENTS.md`, `global/CLAUDE.md` | new `tests/test_runtime_consistency.py` (M10, M11, M13) |
| B2 | Prohibitions with a working way: BA1 to BA4, `gates.sh fix-files`, `gates.sh move` | chief card, executor, surveyor, `kit/scripts/gates.sh`, new move script | unit tests for both commands on Windows paths |
| B3 | Ceremony out: BC1 to BC6 (single write, no TRD Planned, smaller Self-check, silent warnings, `--help`, the one-rule C5) | docs and executor agents, `prd-writing.md`, `trd-planned.md`, `agent-plan.md`, `classification.md`, `gate*.py`, `promote.py` | gate and promote tests |
| B4 | Harness and shape: BE1 to BE4, BF1 to BF3, doctor checks, meta-rules M08 to M13 | `installer/ai-kit` doctor, `SKILL.md`, `MAINTAINING.md` | installer test |

Order: O first and alone (P0: no agent may hang again while the rest is built), then I1, I5 and I11 (the format and its gate), then I2 to I4, I9 and I10 in one wave (disjoint files), then I6 to I8. B1 runs before B3 (both touch the reference files); B2 and B4 in parallel with I6 to I8.

## Targets on the next real C5
| Metric | Today | Target |
|---|---|---|
| User touchpoints before code | 6 to 13 | at most 2 (3 with a follow-up) |
| Repeated topics | 3 to 4 per run | 0 |
| Decisions reversed after the PRD commit | 1 (voz) | 0 |
| `rules.md` edits | 25 to 35 | at most 2 per rule row |
| Gate reruns in the docs phase | 5 to 7 failures | at most 1 |
| Stuck agent minutes (alive minus tool time) | about 230 (f57d6438) | 0 |
| Orphan processes at a wave end | 6, then 1 more | 0 |
| Heredoc commands | 53 | 0 |
| Questions after the plan was approved | 5 | 0 |
| Agents over 150k tokens | 7 | 0 |
| Interview and docs tokens / code tokens | 2.06M / 1.72M | below 1 |

## Track B: instructions that make behavior worse
Same kind of problem as the 16 dimensions: context that an agent follows faithfully and that makes it slower or wrong. Sources: `kit-contradictions.md` (21 contradictions, 10 dangling references, file:line on both sides) and `instruction-misbehavior.md` (sessions 9528886a and f57d6438, 61 subagent transcripts, the chief's own audit), scratchpad of session 5dcb60e5.

### B-a. Prohibitions that block the obvious action
| ID | Instruction | What happened | Fix |
|---|---|---|---|
| BA1 | Chief card: "Forbidden: preparing a question" | Chief, in its own audit: "the skill forbids me to rewrite a question, so I could only pass it on"; one question asked 3 times, the user: "I did not understand, more details" | The chief may explain and rephrase a question with today's rule, and read the PRD rows the sheet cites |
| BA2 | Executor: "no related tests, suites, gates or lint runs" | 7 of 9 closes of 2026-10-09 failed on lint after 10 to 18 min of tests; 7 commits only for lint | Executor runs format and lint on its own files before each commit (`gates.sh fix-files <files>`) |
| BA3 | "Move code by script, never retype" plus "no `python -` heredoc" plus "edit with Edit", with no shipped move tool | 6 executors stuck 14 to 56 min on hung heredoc shells (over 4 h of agent time); one ran `taskkill /IM python.exe` | Ship `gates.sh move <src> <range> <dst>`; the rule applies only to C6 refactors; elsewhere Edit |
| BA4 | DP01 "a prompt carries no domain assumption", surveyor reads only PRD and code | Recommendations contradicted a preference the user had already given; 2 corrections | The chief passes the user's stated preferences verbatim (memory and this conversation) as `Preferences:` |

### B-b. Contradictions between files (the agent picks one)
| ID | Side A | Side B | Cost seen |
|---|---|---|---|
| BB1 | Agents: long commands foreground, timeout up to 600000 | global/CLAUDE.md, AGENTS.md, DP02: background | 11 waits of 580 to 591 s, about 130 min of blocked agents |
| BB2 | reviewer.md:39, recheck.md:28: Medium goes pending | review.md V04, SKILL.md: Medium goes to a fix and counts a round | 3 extra user round trips, close run twice |
| BB3 | agent-plan.md:94 (copied into every plan): close runs the full suite | E18, E20, V09, DP07: the chief runs `compare`, close reuses it | Close ran the suite inline, 10 to 18 min each |
| BB4 | prd-writing.md:19, trd-planned.md:61, agent-plan.md:23: separate `gate.py --step` calls, 2 reruns | docs agent, DS46: one `gates.sh docs`, one rerun | Extra gate runs per docs dispatch |
| BB5 | agent-plan.md:23: docs starts the baseline with `--bg` | DP06: only the chief, never `--bg` | Baselines inside docs agents (LS31) |
| BB6 | kit/CLAUDE.md:27, AGENTS.md:40: run related tests | Executor: only its own test; Self-check demands "structure tests ran, green" | An executor cannot be honest and compliant at once |
| BB7 | C4 ends in executor close | Baseline starts only for C2, C3, C5, C6 | Every C4 close fails "baseline missing" |
| BB8 | Agents: 15 lines plus five fields | global and AGENTS.md: 20 lines Done/Files/Tests/Gaps | Return format drift, "return the five fields" re-dispatches |
| BB9 | Surveyor and docs `model: opus` | "sonnet by default, opus with a written reason" | Cost |

Root cause: the orchestration rules (review policy, verification, full suite, baseline) live in six places (SKILL.md, execution.md, review.md, agent-plan.md, the docs Plan step that pastes two paragraphs into `## Plan`, and the plan header). Fix: one home per rule (M02), the others link by heading; drop the pasted `Execution:` paragraphs and the plan header copy.

### B-c. Ceremony that a gate or a template demands without product value
| ID | Instruction | Fix |
|---|---|---|
| BC1 | Every doc is written twice: PRD row with the pending marker then stripped by promote; TRD Planned then merged into the body; DEC rows in decisions.md, the CHANGELOG draft and the promote entry; the plan header copying the execution rules | Write once: PRD rows final (the change folder says what is pending), no TRD Planned (the plan cards already map files), DEC only in decisions.md |
| BC2 | Executor Self-check of 7 lines (PII, soft-delete, tenant scope, key-off parity...) for every task | Only the lines the card's Lens or rules ask for |
| BC3 | Gate warnings the agent must ignore: G25 printed 111 times across 15 agents, G29 and G32 "run /docs-html" 20 times although prd-flow must not run it, G28 9 times, Q9 false positive on pt-BR (the regex knows only English) | A warning that needs no action is not printed; Q9 goes with the sheet |
| BC4 | Flags documented only in `gate.py` source | Two surveyors read the source to find them: `gate.py --help` lists every flag, the agent files name the exact command |
| BC5 | Size M (brief.md plus plan.md) is the minimum C5: a one-row change pays brief, TRD, plan, baseline, waves, review and promote | A one-rule C5 with one task: sheet, PRD row, one card, close. Brief only for size L |
| BC6 | E01: a fresh session is mandatory with more than 2 waves left | Only past about 120k tokens in the chief, as an offer |

### B-d. Unreadable or dead context
| ID | Instruction | Fix |
|---|---|---|
| BD1 | Rule IDs from `rules/` (TS45, SA51, LT01 to LT12, RV18, WF72...) cited in runtime files; `rules/` is not installed in projects, and LT and RV18 are not even in the catalog | Runtime files cite only headings of files the agent loads; IDs stay in `rules/` |
| BD2 | "context 6 lines, round 25" (SKILL.md) defined nowhere; CE12 limits plus R07 "no IDs" plus the plain-words lint strip the context out of questions | Replaced by the sheet format |
| BD3 | interview.md title says step 4, SKILL.md says step 3; E04 points to a line that lives in dispatch.md; agent-plan.md:103 says executors get the plan path, E15 says they read it from `## Plan` | Fixed by the one-home rule |
| BD4 | Constitution numerals in kit/CLAUDE.md differ from the constitution template | Generate the index from the template |

### B-e. Clashes with the harness and the settings
| ID | Clash | Cost | Fix |
|---|---|---|---|
| BE1 | `settings.json` denies `Read(./CHANGELOG.md)`; prd-flow must write the CHANGELOG | 6 denied calls, 2 user questions, docs gate red over 1 h | `/ai-kit doctor` and the surveyor's batch 1 check that the files the flow writes are readable and writable; a denial is never a product question |
| BE2 | Harness attribution reminder versus the project's no-trailer rule | One commit amended | The executor commit line says which trailer wins |
| BE3 | Harness: subagents return findings as text; the reviewer writes `findings-r<N>.md` | 2 blocked writes | Findings in the return text; a file only past the line cap, named in `Files:` |
| BE4 | Instructions mandate chained commands (`git add ... && git commit -F -`, format and commit) that the permission classifier blocks | 5 denials, each a user round trip | One command per call |

### B-f. Flow shapes that do not fit real work
| ID | Shape | Cost | Fix |
|---|---|---|---|
| BF1 | One slug per repository, no multi-repo change | 3 runs for 1 problem; confirmations tripled; a fourth surveyor (92 calls, 45 state edits) only to align names | One slug, one sheet, rows grouped by repository (`.ai-kit/repos.json`) |
| BF2 | The survey runs before asking where the change lives | Survey in the wrong repo, slug closed, rules discarded next day | Where the change lives is the first line of the request check, before any survey |
| BF3 | Three slugs in parallel in one working tree | Cross-slug verify, lint and edits (audit 2026-10-09 problem 5) | The chief refuses a second slug in the same tree; a worktree per slug |

### Meta-rules for writing kit instructions (to add to MAINTAINING.md)
| ID | Rule | Check |
|---|---|---|
| M08 | Never forbid without naming the allowed way that works on Windows, macOS and Linux | Review of every "never" line |
| M09 | A gate checks product content; an error that only checks the form of a record, or a warning that needs no action, is removed | Count of gate codes per run in the eval |
| M10 | One home per rule; other runtime files link by heading, never restate | A test that flags the same sentence, or the same number with different values, in two runtime files |
| M11 | Runtime files cite only what the agent can open | A test that every cited ID or heading resolves inside the installed files |
| M12 | Every instruction is checked against the harness (system reminders, settings deny, permission prompts) | `/ai-kit doctor` |
| M13 | Read budget per mode: at most 3 reference files before the first action | A test on the agent files |

## Risks
| Risk | Mitigation |
|---|---|
| A free-text answer is misread | The approval shows the rule diff as written (today, then new); a correction is an in-place `adjust` |
| A long sheet is hard to read | The diff first, decisions capped at 8 with a recommendation each, `ok` accepts all |
| The user stops halfway | Unanswered items take the recommended default only if the user says `ok`; otherwise they stay open and nothing is written |
| Repositories on the old format | `/ai-kit update` brings the new references; a state folder from an old run finishes on the old route (`resume` reads its files) |

## Decisions for the user
| ID | Decision | Recommendation |
|---|---|---|
| Q1 | Answer channel | Chat, free text by number (no AskUserQuestion in the interview) |
| Q2 | Cap of decisions per sheet | 8; more means split the change |
| Q3 | Follow-ups | One; then `Q-` rows with the default, visibly open |
| Q4 | The 16 dimensions | Decided by the user on 2026-10-09: removed ("não precisamos de todas aquelas regras, 16 dimensões, isso tá trazendo ineficiência"); one blind-spot line in the surveyor file; clinical safety (clara-ai D16) stays a protected rule |
| Q6 | Track B (instructions that make behavior worse) | Same branch, waves B1 to B4 after I1 to I5 |
| Q5 | Branch | Continue on `feat/run-speed` (it already replaced round 0 and the question lint in 730dd4a, which this plan supersedes) |

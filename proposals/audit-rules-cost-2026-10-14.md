# Audit: the cost of the rules themselves (2026-10-14)

Status: proposal, waiting for the owner's yes. Read-only audit of the ai-starter-kit (`main` checkout), clara-ai, agora-consulta-fe and modulo-integrador (all on `origin/staging`). Owner's direction: clear rules, fewer scripts, many changes must become viable again.

Evidence keys: `R1..R16` are the frictions of `eval/audit-2026-10-14-session-slowness/run-013-frictions.md`; `F01..F12`, `D01..D06` are `FINDINGS.md` of the same folder; `A1..A6` are new facts found by this audit:

| ID | Fact |
|---|---|
| A1 | The kit catalog holds 434 rule IDs in 11 files (`rules/*.md`), plus about 45 gate codes (G0 to G32, Q1 to Q5, S0 to S6, P1 to P10) and 40 `gates.sh` targets. Each adopting repository restates a subset in `CLAUDE.md`, `AGENTS.md`, the constitution and the code-structure doc |
| A2 | Shrink-only allowlists on staging: clara-ai `untested_rules` 278, `duplicate_names` 8, `crowded_dirs` 4 exact counts; agora-consulta-fe `no_prd_id` 656, `untested_rules` 129, `duplicate_names` 13; modulo-integrador `no_prd_id` 1,165, `duplicate_names` 104, `untested_rules` 125, `no_feature_map` 22. `ratchet.py` fails when an entry "dropped, lower the entry" (lines 152, 166 to 174): removing a file also costs an allowlist edit |
| A3 | clara-ai `tests/unit/test_architecture.py` (1,198 lines) re-enforces module, function, class and test size, banned names and PRD ID headers that `ratchet.py` already enforces, and carries about 880 lines of import-edge allowlist (`_BAD_IMPORTS_RAW` plus `BAD_IMPORTS`, `features.X:profundo` deep imports) plus per-class line counts (`Settings`: 393) |
| A4 | The kit's own M09 says "a gate checks product content; an error that only checks the form of a record ... is removed", yet S0, S1, P1, P2, P10, Q1, Q5, G2, G3 and G9 are form checks that error |
| A5 | agora-consulta-fe `CLAUDE.md` tells every session to read `specs/008-unit-config-tokens-fe/plan.md` while its `AGENTS.md` says `specs/` is legacy and never read; `AGENTS.md` "Keeping it true" still says to move superseded wording to `docs/prd/CHANGELOG.md` (frozen by DS12) and "Workflow" still requires `decisions.md` and `plan.md` for size M and a Promote step (both retired by rule-as-data) |
| A6 | The guard hook blocked this read-only audit agent from piping `git show` into a temp file (`A shell redirect writes a source or doc file`): the deny list fires on harmless analysis, not only on source edits |

## 1. Verdict

Yes: the rules are a main cause, not only the orchestration pattern. Each commit pays for traceability copies (PRD row with markers, INDEX IDs, module ID header, test ID, TRD row, area map, trailer, commit-body record), and exact-count structure allowlists in 2 enforcers. Each task pays for a 13-field card, a 50-call ceiling and a cold handoff.
These duties produced 45% docs and 32% review agent time against 14% implementation (F02), and a 36% docs-gate failure rate on bookkeeping (D02).
Fewer than a fifth of the rules protect a patient, personal data or production. The others protect the process from itself.
Proposal: 25 rules (section 4). Mechanical checks only for safety, secrets, offline tests and cheap linter rules with file-list baselines. Traceability and TRD sync are checked once per delivery by the reviewer. Delete the exact-count allowlists, `duplicate_names`, the module ID headers, trailers, plan/sheet/pack lint and the INDEX ID column.
The change is mostly deletion. It adds no script.

## 2. Cost map

Unit: T = per task, C = per commit, D = per delivery, E = per edit near a limit. Verdicts: KEEP (protects patients, data or production, or is a cheap check that never needs a per-change edit), SIMPLIFY, MOVE TO REVIEW, REMOVE.

### Code structure

| # | Rule or gate | Source | Demands | Unit | Cost evidence | Verdict and how |
|---|---|---|---|---|---|---|
| 1 | Module up to 500 lines | AR03; `ratchet.py` long_modules; FE `eslint.structure.mjs` max-lines; clara `MAX_MODULE_LINES` | Split a file the moment a feature pushes it over | E | R1 (`text_turn.py`, FE `use-conversation-session.ts` callback moved and retyped, `reader.py` 507) | SIMPLIFY: one enforcer (linter), checked at the wave verify and CI, not per task; a file over the limit is split once, in a refactor commit at the end of the delivery, never mid-feature |
| 2 | Function up to 80 lines | AR03; linter; clara `LONG_DEFS` | Split functions mid-feature | E | R1 (`_open_encounter` 84) | SIMPLIFY: same as 1; file-list baseline, no counts |
| 3 | Class up to 300 lines, per-class count allowlist | AR03; clara `LONG_DEFS` `Settings: 393` | Bump an exact count when a settings field is added | E | R4 (393 to 398) | SIMPLIFY: exempt declarative classes (settings, schemas, models) by name; never a line count in an allowlist |
| 4 | At most 5 parameters | AR24; FE `max-params` 5; clara `too-many-arguments` | Parameter objects created to pass the linter | E | R1 (`_TurnReads`, `AgentInputs`, `build_agent_context` 10) | SIMPLIFY: 7, keyword-only arguments and React props objects not counted |
| 5 | Complexity 10, nesting 4, nested callbacks 3 | AR24; linter with baseline | Nothing unless violated | none | not observed | KEEP (cheap linter, file baseline) |
| 6 | `crowded_dirs` with exact counts | AR23; `ratchet.py`; `ai-kit.allowlist.json` | Bump or lower a count on every add or delete in a crowded folder | C | R2 (models 25 > 24, socket 31 > 29, relay 41 > 40; modules placed in the wrong package to dodge the cap; several agents editing one allowlist) | REMOVE from the ratchet; one guideline line in the code-structure doc ("split a folder past about 20 files, as its own refactor") |
| 7 | Exact-count shrink-only allowlists ("dropped, lower the entry") | AR15 to AR17; `ratchet.py` 152, 166 to 174 | An allowlist edit when a violation grows and also when it shrinks or disappears | C | R2, R4; allowlist edits 2% of all edits in run 013 | SIMPLIFY: allowlists are file lists; growth of a listed file is allowed until the delivery's refactor commit; a stale entry is a warning |
| 8 | Unique file names repo-wide | AR02 `duplicate_names` | Rename new files that collide with any file anywhere | C | R3 (`conversation_state_sections.py`, TRD left stale); A2 (104 allowlisted in modulo-integrador, NestJS repeats names) | REMOVE (the path disambiguates; Grep and Glob return paths) |
| 9 | Banned generic names (`helpers`, `utils`...) | AR02 | Nothing unless violated | none | not observed | KEEP (cheap, never a per-change edit) |
| 10 | PRD IDs in the header of every area module | AR06; `ratchet.py` no_prd_id; clara `NO_PRD_ID` | Header edits in every touched module, a third copy of the rule-to-code link | C | R6; A2 (656 and 1,165 allowlisted: the rule bites only new files) | REMOVE (the PRD `Source` column names the file; a test name or docstring cites the ID it proves) |
| 11 | Area map `CLAUDE.md` updated in the same commit | AR07; kit `CLAUDE.md` Traceability; `ratchet.py` no_feature_map | Map edits during tasks | C | R5 (12 map edits in one run) | SIMPLIFY: a map holds responsibility, entry point and TRD link only (no piece list), so it changes only when an entry point moves; updated in the delivery's last task |
| 12 | Import direction with per-edge allowlist and deep-import (`:profundo`) edges | AR08, AR09; clara `test_architecture.py` `BAD_IMPORTS` | An allowlist line per new cross-feature import | C | R4 (`test_architecture.py` edited 25 times by 5 agents); A3 (about 880 lines of edges) | SIMPLIFY: keep the directions that matter (no cycles; core features never import peripheral ones; nobody imports `voice` or `text`; shared code never imports a route), as linter rules without per-edge allowlists; the deep-import rule (AR08) goes to review |
| 13 | Two enforcers for the same structure rule | clara `test_architecture.py` plus `ratchet.py` plus `ai-kit.allowlist.json` | Two allowlists to bump for one violation | C | R4; A3 | REMOVE the duplicates: one rule, one enforcer |
| 14 | Move code by script, never retype | AR12, SA26, global "Editing" | `gates.sh move` with line ranges | E | R1 (ignored: callback retyped) | KEEP as one behavior line (prevents transcription bugs that reach production); no gate |
| 15 | Dead code, duplication, typing only goes up | AR25 to AR27 | Nothing unless violated | none | not observed | KEEP (linter baselines) |
| 16 | Generated markers, layout config validation | AR19, AR28 | Nothing unless violated | none | not observed | KEEP |
| 17 | Ratchet run with the related tests of every task | AR18 | A ratchet run per task | T | contradicts TS51, TS53 | REMOVE (the wave verify and CI run it) |

### Docs

| # | Rule or gate | Source | Demands | Unit | Cost evidence | Verdict and how |
|---|---|---|---|---|---|---|
| 18 | PRD row format `ID, Rule, Source file::symbol, Change via, Example` | DS05, DS07, DS08, DS32; G3 | Five cells per row, Change via from a closed list, Example column | C | R8 (40 rows rewritten for one change); D02 | SIMPLIFY: `ID, Rule, Source (file)`; Example optional; no gate on Change via values |
| 19 | Status markers `(approved date, pending code)`, `planned`, `proposed` | DS09, DS13, WF33, WF37; G9, G19, G30 | Writing then flipping markers task by task | C | R8; 88 marker occurrences in clara-ai `docs/prd` (staging) | REMOVE: a row is today's behavior or it is not in the PRD; an unconfirmed rule sits in the section's open questions; one-time cleanup of existing markers |
| 20 | INDEX IDs column regenerated by `gen_index.py`, G2 | DS02, DS47 | `gate.py --fix` after every row change | C | R8; D02 (G2 among the top failing codes) | REMOVE the IDs column (`Grep "<ID>" docs/prd` finds the file); INDEX lists files and their TRD, so it changes only when a file is added |
| 21 | PRD section and TRD line budgets | DS36, DS44; G26, G31 | Splitting doc files during a feature | C | R8 (28-maestro 225, 26-12 312, questionnaire 274, voice 268); D02 (G31) | REMOVE as gate codes; one guideline: split a doc file past about 300 lines, in a docs-only commit outside feature deliveries |
| 22 | Docs gate with about 45 error codes | DS24, DS26, DS46, WF68, WF73; `gate.py` and `gate_*.py` | Rerun until green; form errors on state artifacts | C, T | D02 (166 of 459 runs failed); R7 (106 calls fixing 50 gate errors); A4 | SIMPLIFY: errors only for G1 (duplicate ID) and G8 (cited ID missing); G4 em dash moves to the linter; G23 TRD path and G28 shared PRD stay warnings; delete G2, G3, G9, G11, G12, G14, G16 to G21, G24 to G27, G29 to G32 outside docs-html, every Q, S and P code |
| 23 | Every changed rule has a test citing it; `untested_rules` allowlist | WF31, TS15; G12, G14 | A named test per rule ID, or an allowlist line | C | R7 (50+ named tests, many structural, guessed paths); A2 (278, 129, 125 entries) | MOVE TO REVIEW: the reviewer checks each acceptance item has a test; tests cite an ID when they prove a rule; delete the allowlist |
| 24 | TRD body updated in the same commit as the code | AR13, DS15, DS21; kit `CLAUDE.md`; executor "Rule rows with the code" | TRD edits in every task | C | R5 (104 TRD edits in one run, "Planned" written then moved task by task) | MOVE TO REVIEW: the delivery's last task updates the TRD (files and entry points only); the reviewer checks names exist |
| 25 | TRD content checks (cited symbols exist, IDs mentioned, no values) | DS33, DS37; G24, G25 | Rewording TRD rows to satisfy checks | C | R3 (TRD stale anyway) | MOVE TO REVIEW |
| 26 | Grep the old value over all of `docs/` and open change folders before each commit | executor "Rule rows" step 1; DS33 | A repo-wide docs sweep per rule-changing commit | C | R14 (reading load) | MOVE TO REVIEW (one sweep per delivery) |
| 27 | Invariants, each with a proof (test or principle), `invariant_gaps` ratchet | DS19, DS31, DS38 | A structural test or a gap count per invariant | C | R5 (12 invariant edits); clara 109 invariants; FE 8 gaps | SIMPLIFY: `invariants.md` is the reviewer's checklist by kind of change; tests only for invariants that protect patients, data or production; delete the gap count |
| 28 | CHANGELOG frozen | DS12 | Nothing (removed work) | none | R9 (rollout mid-run caused a merge conflict); A5 (FE still says to append) | KEEP the freeze; finish the rollout in the repositories' `AGENTS.md` |
| 29 | Commit body record `Request:`, `Decided:`, `Assumed:`, `Red:`, `Rules:` | DS12, CE29, kit `CLAUDE.md`; executor | Five labeled fields per commit | C | R11 | SIMPLIFY: only a commit that changes a PRD row carries `Decided:` lines (the user's choice, verbatim); no `Red:`, no `Assumed:` block |
| 30 | Commit trailers `Rules:` or `Case: none (...)` | WF49; `commit_trailers.py`; `gates.sh trailers`; CI | A trailer per commit touching source, checked in CI | C | R11 | REMOVE (the PR description lists the IDs; the PRD diff shows them) |
| 31 | HTML pages and stale-page warnings | DS14, DS42, DS45, DS48; G5, G29, G32 | Warnings on every gate run; rebuild before sharing | D | D02 (G5 and G29 top failing codes) | SIMPLIFY: only `/docs-html` builds or checks; delete the warnings from the default gate and CI |
| 32 | Change folders by size (S none, M decisions and plan in older copies, L brief, design, plan, decisions) | WF26, WF27, DS49; FE `AGENTS.md` "Workflow" | Up to 4 files for size L | D | R14 (design 288, rule-changes 520+, plan 203 lines, reread by every executor) | SIMPLIFY: size L gets one `plan.md` (decisions, slices, acceptance items); S and M none |
| 33 | Plan header `## Constitution check` | WF28 | A table per plan | D | not observed | MOVE TO REVIEW (the risk reviewers read the constitution) |
| 34 | Decision sheet rules and sheet lint S0 to S6, Q3 mechanism check, follow-up sheet | WF10, WF15, WF42, WF43, WF67 to WF69, WF75; `gate_interview.py` | Lint-passing sheet before the user sees it | D | memory: the interview cost more than the code; F05 (hours waiting on answers) | SIMPLIFY: one guideline (at most 8 decisions, today vs proposed, a recommended option each, product words); no lint |
| 35 | Surveyor sweep K01 to K14 with `prd_sweep.py` | WF11, WF38 to WF41, WF57, WF83 | 14 checks per rule change | D | WF83 itself: 37 to 118 surveyor calls | SIMPLIFY: a 4-item checklist (Grep IDs and terms in `docs/prd`, sibling consumer contract, safety nets touched, history of the IDs) |
| 36 | Pack, card, sheet, deliveries, facts, state.md ledger | SA05, SA07, SA49, SA50, CE23, CE24, WF64 | State artifacts with formats and gates (Q1) | T, D | D04 (`state.md` 358 KB, 26 reads in one change) | REMOVE for S and M; size L keeps only `plan.md` |
| 37 | Rule owners, owner agreement before closing the interview | WF48, DS43 | A statement per change in another owner's area | D | not observed | SIMPLIFY: CODEOWNERS on the PR does it; drop the interview step |
| 38 | Shared PRD identical in sibling repositories | DS39; G28 | A copy when a shared PRD changes | D | not observed | KEEP as a warning (a divergent shared PRD misleads two teams) |
| 39 | ADR for a protected rule | DS23, DS27, DS28, WF13 | Rare | D | not observed | KEEP (protects safety nets) |
| 40 | Language: everything English (kit) vs pt-BR PRD and TRD (clara-ai) | WS01, M05, constitution template; clara `CLAUDE.md` | Agents switch language per file | C | R15 | SIMPLIFY: code, commits and agent files in English; PRD and TRD in the language each repository declares once in `CLAUDE.md`; UI copy in the product locale |
| 41 | No em dash | WS02; G4; clara I-01 | Fix loops when an agent writes one | C | not measured | KEEP as one lint on added lines (cheap) |

### Orchestration, tests, safety

| # | Rule or gate | Source | Demands | Unit | Cost evidence | Verdict and how |
|---|---|---|---|---|---|---|
| 42 | Ceiling about 50 calls or 30 min; replacement past 150k with a 10-line handoff | global block; SA15, SA16, SA19, RV08; `run.md` V08 | A cold handoff at every ceiling | T | R12 (many handoffs, then lanes of 120 to 200 calls at 400k to 490k); F10 (17 agents over 150k); SA63 (12 orienting calls per cold start) | SIMPLIFY: one ceiling, about 150k tokens; at the ceiling or when the slice ends, the executor reports to the user what is left; no automatic replacement lane |
| 43 | Task cards with about 13 fields, gate P1 to P10, waves computed | SA22, SA36, SA37, WF19, WF74; `write.md` "Card"; `gate_waves.py` | Card fields `Depends on`, `Read`, `Model`, `Lens`, `Reached from`, `Owns`, `Leave`, `Commit` | T | R7 (106 calls on plan format) | SIMPLIFY: a task is one line (slice, files or area, acceptance items); no gate |
| 44 | Plan maps each item to a task and a test (SA64) | global block; SA64 | A named test per rule ID before dispatch | D | R7 (50+ named tests with guessed paths) | SIMPLIFY: map acceptance items (or findings) to slices; tests are named by the executor; the reviewer checks the list once |
| 45 | One phase per session; checkpoint past 120k; plan over 6 tasks in a new session | SA61, SA41, CE17 | Session handoffs by file | D | R13 (ignored when scope widened) | SIMPLIFY: size L runs in two sessions (decide and plan; execute); S and M in one; checkpoint past 120k |
| 46 | Scope in three lines and a yes before the first dispatch | SA62, SA60 | One message | D | R13; E1 of the plan (269 files in one delivery) | KEEP (cheap; it is the rule that stops a widened delivery), with an estimate in minutes added |
| 47 | Area-sized tasks, 12 or fewer, at most 4 executors | SA63, SA34, SA35 | Wave planning | D | R12; 13 files edited by 3 or more executors in run 013 | SIMPLIFY: at most 2 executors, each owning one slice for the whole delivery |
| 48 | Executors run only their own new test | global "Tests"; TS51, TS53 | Cross-lane breakage found at the wave or close | T | R10 (architecture test, 3 stale API tests and a hanging test found hours later) | SIMPLIFY: before handing back, the executor runs its tests plus the tests importing the files it touched, with a per-test timeout; full suite once per delivery |
| 49 | Per-wave verify, background baseline, compare, watch, cleanup and reap at every case | TS43, TS50, TS53, SA57 to SA59, WF81 | 4 to 6 chief commands per wave | D | F10; R10 | SIMPLIFY: baseline once, compare once; reap and a `SessionEnd` cleanup hook stay as tools; drop `watch` and per-case cleanup duties |
| 50 | Red proof `gates.sh red` and `Red:` line | TS52 | A failing run recorded per task | T | not measured | SIMPLIFY: test first stays (constitution); drop the recorded proof |
| 51 | Executor self-check block and delivery ledger | SA07, SA52 | `deliveries/<task>.md` per task | T | not measured | REMOVE (the diff and the review are the record) |
| 52 | Chief with a closed tool list; agents commit; surveyor first in every case | SA28, SA43, SA44, SA47 | Extra dispatches for trivial steps | D | F01 (70 to 121 dispatches per long session) | SIMPLIFY: the main may run gates, git and short reads; the surveyor runs only for rule changes |
| 53 | Two return formats (Done/Files/Tests/Gaps, and Status/Files/Commit/Route/Next) | global block; SA06, SA45 | Agents follow one or the other | T | conflict | SIMPLIFY: one format, at most 15 lines |
| 54 | Review at most 5 rounds, once per delivery, scoped recheck | RV01 to RV07, SA40, global | Recheck against the fix diff | D | F02 (review 32%) | KEEP (it catches production defects: 7 High in run 013), and delete RV18's "review per wave stays" |
| 55 | Risk reviewers (clinical, security, contracts) and cross-repo contract check | RV13 to RV16, SA65 | One message at the final review | D | E1 (PII in a new table, cross-repo frame with no reply) | KEEP |
| 56 | Model sonnet by default | global; SA14, SA33 | Pass `model` | T | F11 (47% of turns on Opus); D05 (docs agent pinned to opus) | KEEP, and set `prd-flow-docs` to sonnet |
| 57 | Guard hook denials | SA56; `guard_hook.py` | Commit messages via a file; no redirects, `tee`, `cat >`, heredocs | C | R11; A6 (blocks read-only analysis) | SIMPLIFY: keep git-destructive commands in a shared tree, interpreters reading stdin, heredocs and kill-by-name (measured hangs, LS32); drop redirect, `tee` and `cat >` denials for paths outside the repository's source and docs folders |
| 58 | Executors run `fix-files` and `lint-files` on their files | WF80 | Two commands per task | T | not observed | KEEP (cheap linter, catches style before review) |
| 59 | Test first, offline, deterministic fakes | TS01, TS11, TS12; constitutions | Write the test first | T | none | KEEP (offline guard protects shared databases: modulo-integrador `.env` points to a shared AWS database) |
| 60 | No assertion loosening, no snapshot regeneration to pass | TS09, TS39 | Review | T | F09 (22% of next edits after a failure touched a test) | KEEP (protects production) |
| 61 | Full suite once per delivery against a baseline | TS03, TS04 | One run | D | F06 | KEEP, plus a per-test timeout in the runner config (R10 hang) |
| 62 | PII, PHI and tokens never in URLs, logs, analytics, storage | FE constitution I; clara constitution V and AGENTS #2; CX06 | Review | C | E1 (unmasked PII in a new table) | KEEP |
| 63 | Secrets never in source; gitleaks in CI | CX02, CX10 | CI job | none | none | KEEP |
| 64 | No branching on tenant; per-tenant behavior is config | CX04; repo AGENTS | Review | C | none | KEEP |
| 65 | Clinical safety, parity and rollback (clara I, II, IV) | clara constitution | Review plus structural tests | C | none | KEEP |
| 66 | spec-kit workflow, `/orchestrate` pipeline and prd-flow described side by side | FE `AGENTS.md` "Feature Development Workflow"; FE `CLAUDE.md` plan pointer | Agents read three workflows and a stale plan | session | A5 | REMOVE the spec-kit section and the plan pointer from the always-loaded files (keep the skills on demand) |
| 67 | Docker hygiene TS27 to TS36 | rules 04; global block | Only when a test builds images | rare | not observed in these repos | KEEP (disk guard; no per-change cost) |
| 68 | Telemetry hooks and retro | TM rules; `settings.json` | Async hooks; retro at close | D | not observed as cost | SIMPLIFY: hooks stay; the retro runs on demand, not as a close duty |

Tally of the 68 rows: KEEP 22, SIMPLIFY 29, MOVE TO REVIEW 5, REMOVE 12.

## 3. Duplicates and conflicts

### The same rule in several homes

| Rule | Homes |
|---|---|
| Size caps 500/80/300/1,200 | kit `CLAUDE.md`, `docs/code-structure.md` AR03, `rules/05` AR03, each repository's `CLAUDE.md` and code-structure doc, `ratchet.py`, the linter, clara `test_architecture.py` (7 homes, 3 enforcers in clara-ai) |
| Traceability (IDs in modules and tests, TRD and map in the same commit) | kit `CLAUDE.md`, AR06, AR07, DS21, TS15, constitution III, executor agent, each repository's `CLAUDE.md`, `AGENTS.md` "Keeping it true" |
| Ceilings | global block (50 calls or 30 min), SA15, SA16, RV08, `run.md` V08 (surveyor and docs 80, reviewer 40, recheck 15), WF52, plan O3 (120 calls) |
| Test scope while working | global block twice ("Working with subagents" and "Tests"), TS02, TS07, TS51, TS53, RV09, kit `CLAUDE.md`, each repository's `CLAUDE.md` and `AGENTS.md` |
| Background and long commands | global block twice, TS34, TS45, TS54, SA54, WF79, kit `CLAUDE.md` "Processes", repository `CLAUDE.md` and `AGENTS.md` |
| Kill by image name | global block, SA57, kit `CLAUDE.md`, each repository's `CLAUDE.md` and `AGENTS.md` |
| Move code by script | global "Editing", AR12, SA26, kit `CLAUDE.md`, repository `CLAUDE.md` |
| Commit record and trailer | DS12, WF21, WF44, WF49, CE29, kit `CLAUDE.md`, executor agent, FE `AGENTS.md` "Workflow" 3 |
| Return format | global block, SA06, SA45, kit `CLAUDE.md` "Returns", run.md "Every agent", each agent file |
| No em dash | WS02, M05, AGENTS constraint 5 or 11, clara invariant I-01, gate G4 |
| Order of authority | DS01, WF30, kit `AGENTS.md`, FE `AGENTS.md`, constitution Governance |

### Contradictions

| # | Conflict | Sides |
|---|---|---|
| K1 | Ceiling numbers | global block 50 calls; V08 80 for surveyor `full` and docs `plan`, 40 reviewer, 15 recheck; plan O3 120; observed lanes 120 to 200 |
| K2 | Test scope during a task | TS02 and AR18 (related tests and the ratchet with every task) vs TS51, TS53 and the global block (only the own new test) |
| K3 | Who runs long commands in the background | TS54 ("a suite runs with `run_in_background`") vs TS45, SA54 and the global block (a subagent never uses `run_in_background`) |
| K4 | Review per wave | RV18 title "review per wave stays" vs SA40 and the global block (once per delivery) |
| K5 | What the docs gate blocks on | DS24 ("6 errors only") and M09 (form checks are removed) vs about 25 error codes in `gate_*.py` (S0, P2, P10, Q1, Q5, G2, G3...) |
| K6 | Language | WS01, M05 and the constitution template ("everything in English") vs clara-ai `CLAUDE.md` (PRD, TRD and code-structure doc in pt-BR) |
| K7 | Order of authority | DS01 (constitution, PRD, spec or plan, code) vs WF30 (constitution, PRD, TRD, code; a plan governs only the order of work) |
| K8 | Size M paperwork | kit WF26, WF27 (no folder) vs FE `AGENTS.md` "Workflow" 2 (`decisions.md` and `plan.md`) |
| K9 | CHANGELOG | DS12 (frozen) vs FE `AGENTS.md` "Keeping it true" (move superseded wording there) |
| K10 | Promote | DS18, WF29 (retired for S and M) vs FE `AGENTS.md` "Workflow" 5 (promote and archive every change) |
| K11 | Legacy specs | FE `AGENTS.md` (`specs/` never read) vs FE `CLAUDE.md` ("read the current plan at `specs/008-.../plan.md`") |
| K12 | TRD timing inside one file | clara-ai `CLAUDE.md` "Product rules gate" (TRD in the same delivery) vs its "Traceability" line (same commit) |
| K13 | Task granularity | SA34 (a task is one file and its test, split for parallelism) vs SA63 (area-sized, 10 to 30 min) vs plan O3 (one warm executor per slice) |
| K14 | Stack-free kit | M04 (nothing in `kit/` names a stack) vs executor X04 (hard-coded `vitest` command) |
| K15 | Gates are reminders | TS53 and the global block ("a gate finding is a warning") vs the ratchet, G-codes and trailers in CI, which block |

## 4. The proposed rule set (25)

Each rule replaces the IDs in brackets; every replaced ID not listed in section 6 is retired from runtime files (the catalog keeps them as history).

### Scope and slicing
1. Before the first dispatch, state the goal, the artifact, what is out of scope and an estimate in minutes, and get a yes; a widened scope is a new delivery. [SA60, SA62, CE17]
2. A delivery is one vertical slice (one area or engine, about 30 files or 2 hours, its own PR); bigger work is split into slices before any code. [SA34, SA35, SA63, plan O1]
3. Size L (new data model, contract, external integration) gets one `changes/NNN-<slug>/plan.md` with the decisions, the slices and the acceptance items; size S and M get no folder and no state files. [WF26, WF27, WF28, WF43, WF47, DS49, SA05, SA07, SA64, CE23, CE24]
4. A rule change is shown as today vs proposed, at most 8 decisions with one recommended option each, answered once; the code commit updates the PRD row and its body quotes the decision. [WF10, WF15, WF42, WF67, WF69, WF75, DS09, DS12, CE29]

### Agents
5. At most 2 executors at once, each owning one slice and its files for the whole delivery; parallel slices use separate worktrees. [SA13, SA36, SA53, SA63, plan O3]
6. An executor prompt carries the goal, the acceptance items and the paths; it returns at most 15 lines: done, files, tests, gaps. [SA04, SA06, SA22, SA37, SA45, global return line]
7. An executor stops at about 150k tokens or when its slice is done and reports to the user what is left; nobody opens a replacement lane without the user. [SA15, SA16, SA19, SA48, RV08, WF52, V08]
8. Sonnet by default and `model` passed on every dispatch; opus only with a one-line reason. [SA14, SA33, WF51]
9. A subagent never opens a subagent or a background process; long commands run in the foreground with an explicit timeout and output to a file; never kill by image name. [SA12, SA54, TS34, TS45, TS54, SA57]
10. In a shared tree, never `git stash`, `reset`, `checkout`, `restore` or `commit --amend`; write commit messages to a file and commit with `-F`. [SA53, SA56 git part, WF78]

### Code structure
11. New code goes in its feature's area folder, in a file named after its one responsibility; never `helpers`, `utils`, `shared`, `common`, `misc`, `state`. [AR01, AR02 without uniqueness]
12. Size and complexity are linter rules (module 500, function 80, complexity 10, depth 4, parameters 7) with a file-list baseline; a file pushed over a limit is split once, in a refactor commit at the end of the delivery. [AR03, AR15 to AR18, AR21, AR23, AR24]
13. Dependencies point one way as the code-structure doc declares, with no cycles, enforced by the linter without per-edge allowlists. [AR08, AR09]
14. Move code by script (line ranges or AST), never retype it. [AR12, SA26]

### Docs
15. A PRD row is `ID | Rule | Source (file)`; IDs are never reused; the PRD holds only today's behavior; git is the history (no CHANGELOG writes, no status markers). [DS05 to DS09, DS12, DS13, DS32, WF33, WF37, WF60]
16. The TRD and the area maps name files and entry points only, and are updated once per delivery, in its last task. [AR06, AR07, AR13, DS15, DS17, DS21, DS33, DS36]
17. The docs gate errors only on a duplicate ID or a cited ID that does not exist; everything else is a review item. [DS24, DS26, DS37, DS44, DS46, DS47, WF31, WF68, WF73]
18. Code, commits and agent files are in English; PRD and TRD in the language the repository declares once in `CLAUDE.md`; UI copy in the product locale; no em dash anywhere. [WS01, WS02, M05]

### Tests
19. Write the failing test first; unit tests run offline with fakes and with a per-test timeout. [TS01, TS11, TS12, TS52, new timeout]
20. Before handing back, the executor runs its tests and the tests that import the files it touched; the full suite runs once per delivery against a recorded baseline. [TS02 to TS05, TS07, TS43, TS50, TS51, TS53, global "Tests"]
21. Never loosen a safety assertion or regenerate a snapshot to get green; an unrelated failing test is reported, not investigated. [TS05, TS09, TS39]

### Review
22. One review per delivery over the combined diff of every repository: the acceptance list item by item (each with a test), cross-repo fields from both sides, PRD rows and TRD names; the risk reviewers go in the same message. [SA40, SA64, SA65, RV13, AR06, AR07, DS21, TS15]
23. Critical and High findings are fixed and rechecked against the fix diff only; at most 5 rounds; a worse round, or an open Critical at round 5, stops and asks the user. [RV01 to RV07, RV18, WF82]

### Safety
24. PII, PHI and tokens never reach URLs, logs, analytics or long-lived storage; secrets never enter source (gitleaks in CI). [constitution I (FE), CX02, CX06, CX10]
25. Safety nets (guardrails, alarms, rollback switches, tenant configuration) change only with a person's explicit yes, never inside a task, a fix or a test edit. [WF12, WF13, RV06, CX04, CX07, clara constitution II and IV]

## 5. What to delete or relax

### In the kit (one PR to `main`)

| File | ID or gate | Change |
|---|---|---|
| `global/CLAUDE.md` | "Working with subagents", "Orchestrating a delivery", "Tests" | Replace with rules 1 to 10 and 19 to 23 (about 18 lines); drop "Gates are reminders", the 50-call ceiling, the two return formats, "executors run only their own new test" |
| `rules/` | all 434 IDs | New `rules/core.md` with the 25 rules and their replaced IDs; the 11 files move to `rules/archive/` as history; `rules/README.md` points to `core.md` |
| `kit/CLAUDE.md` | Code structure block | Keep Where, Size (as rule 12), Shape; delete Traceability, Returns, Processes (now in the global block); Language becomes rule 18 with a per-repository placeholder |
| `kit/AGENTS.md` | Workflow, Keeping it true, Testing while working, gate list | Workflow becomes rules 1 to 4 and 15 to 17; delete "same commit" duties, trailers and promote; gate list keeps `one`, `related`, `verify`, `baseline`, `compare`, `lint`, `fix-files`, `lint-files`, `move`, `reap`, `docs`, `html` |
| `kit/.specify/memory/constitution.md` | III, IV, Development Workflow 2 to 4, "Everything in English" | III: rows land with the code, TRD per delivery; IV: linter, not ratchet; Workflow: rules 1 to 3, 19, 20; language per rule 18 |
| `kit/docs/code-structure.md` | AR02, AR03, AR06, AR07, AR16, AR18, AR23, AR24 | Drop name uniqueness, ID headers, the per-commit map duty, exact counts, AR18, AR23 as a check; parameters 7; class limit exempts declarative classes |
| `kit/scripts/ratchet.py`, `kit/ai-kit.allowlist.json` | `duplicate_names`, `crowded_dirs`, `no_prd_id`, `long_feature_maps`, `invariant_gaps`, `untested_rules`, count values | Delete these checks and keys; allowlists become file lists; a stale entry warns |
| `kit/.claude/skills/prd-flow/scripts/` | G2, G3, G9, G11, G12, G14, G16 to G21, G24 to G27, G30, G31, Q1 to Q5, S0 to S6, P1 to P10 | Delete the codes and the modules left empty (`gate_interview.py`, `gate_rules.py`, `gate_prd.py`, `gate_budget.py`, `gate_waves.py`, `gate_remote.py`, `gen_index.py`, `prd_sweep.py`, `state_record.py`); G1 and G8 stay errors, G23 and G28 warnings, G29 and G32 only under `--html`; G4 moves to the stack linter recipe |
| `kit/scripts/commit_trailers.py`, `gates.sh trailers`, CI job | WF49 | Delete |
| `kit/scripts/gates.sh` | `red`, `watch`, `prd-sweep`, `trailers`, `settings-check`, `context`, `retro` inside `close` | Delete the targets; `close` becomes compare plus lint plus docs |
| `kit/scripts/guard_hook.py` | SA56 redirect, `tee`, `cat >` | Deny only when the target is under the repository's source or docs folders; keep git-destructive, stdin interpreters, heredoc and kill-by-name denials |
| `kit/scripts/verify.py` | E3 of the plan (`default_ref`) | Bug fix only: match `{slug}/plan.md` and `*-{slug}/plan.md` |
| `stacks/*` | TS timeout | One config line per stack (pytest `timeout`, vitest `testTimeout`); not a script |
| prd-flow `SKILL.md`, `reference/*.md`, `.claude/agents/prd-flow-*.md` | SA28, SA43, SA44, SA45, SA49, SA50, SA52, WF64, card format, sheet lint, deliveries ledger, Self-check, `Red:`, executor X04 | Surveyor only for rule changes; chief may run gates and git; one return format; a task is one line; executor: no ledger, no grep-all-docs step, no hard-coded runner; `prd-flow-docs` model sonnet |
| `MAINTAINING.md` | M09 | Extend: "a rule that adds per-commit or per-task work needs a measured defect it prevented; otherwise it is a review item" |

### In each repository (one PR each, from its staging)

| Repository | File | Change |
|---|---|---|
| all three | `CLAUDE.md` | Code structure and process blocks replaced by the update; delete the Traceability line |
| all three | `AGENTS.md` | Workflow, Keeping it true, Testing while working and the gate list per the kit; remove the "move superseded wording to CHANGELOG" line and the promote step (K8 to K10) |
| all three | `ai-kit.allowlist.json` | Drop `duplicate_names`, `crowded_dirs`, `no_prd_id`, `untested_rules`, `invariant_gaps`, `no_feature_map`, `long_feature_maps`; counts become file lists |
| all three | `docs/prd/INDEX.md` | Drop the IDs column |
| all three | `docs/trd/invariants.md` | Proof column optional; it is the reviewer's checklist |
| clara-ai | `tests/unit/test_architecture.py` | Delete the checks `ratchet.py` or the linter already make (module, test and class size, banned names, PRD ID headers) and the `:profundo` deep-import edges; keep cycles, core-to-peripheral, `voice` and `text` not imported; `LONG_DEFS` becomes an exempt-name list (`Settings`) |
| clara-ai | `docs/estrutura-do-codigo.md`, `CLAUDE.md` | Same deletions as the kit template (AR06, AR07 detail, AR23, parameters 7); declare "PRD and TRD in pt-BR" once (rule 18) |
| clara-ai | `docs/prd/**` | One-time removal of status markers (`aprovada ...`, `pendente de código`, `planejado`) by a docs commit, rows kept |
| clara-ai | `pyproject.toml` | Coverage off by default for unit runs (F08), `pytest-timeout` default (R10) |
| agora-consulta-fe | `CLAUDE.md` | Remove the `specs/008-.../plan.md` pointer (K11) |
| agora-consulta-fe | `AGENTS.md` | Remove the spec-kit "Feature Development Workflow" section from the always-loaded file (the skills stay) |
| agora-consulta-fe | `eslint.structure.mjs`, `vitest.config` | `max-params` 7; unit `testTimeout`; unit project without the Storybook plugin (F12) |
| modulo-integrador | `.eslint-structure.js`, `CLAUDE.md` | `max-params` 7; delete Traceability line; per-test `testTimeout` in Jest |

## 6. What stays mechanical

| Check | Mechanism | Reason |
|---|---|---|
| Secrets in tracked files | gitleaks in CI (CX10) | A leaked credential is irreversible even after revert |
| Offline unit suite | the gate sets its own environment; network or database under the offline flag fails (TS12) | The local `.env` of modulo-integrador points to a shared AWS database; a test that reaches it corrupts shared data |
| Per-test timeout | runner config line | A hanging test held run 013 for over 500 s (R10); a config value, no per-change edit |
| Full suite vs baseline, once per delivery | `gates.sh compare` | Production regressions; one run per delivery |
| Clinical guardrail and parity tests (clara-ai IV, I) | existing structural tests | A model output reaching a patient unguarded is the worst defect class of the product |
| Git-destructive commands, stdin interpreters, heredocs, kill by image name | guard hook | Lost sibling work and 230 stuck agent-min were measured (LS32); the hook needs no per-change edit |
| Size, complexity, dependency direction, dead code, typing | stack linter with a file-list baseline | Cheap, no allowlist edit per change once counts are gone |
| Banned generic names, generated markers | `ratchet.py` | Cheap, never a per-change edit |
| Duplicate PRD ID, cited ID missing | `gate.py` G1, G8 | A wrong ID misleads code, tests and people; cheap |
| Em dash on added lines | linter or G4 | Cheap; house style that agents break by habit |
| Conventional Commits | commitlint hook | Already in place, no per-change work |
| CI timeouts and cancel rules | TS23 to TS25 | A deploy whose check never concluded reaches production |

Everything else (traceability, TRD and map sync, invariants coverage, plan shape, decision sheet shape, constitution check) is a reviewer check once per delivery.

## 7. Revised plan (replaces "Changes" and "Execution" of `plan-right-sized-deliveries.md`)

Keep from that plan: O1 (as rules 1, 2), O3 (as rule 5, with 2 executors and no call ceiling), O4 (design review for size L folds into rule 22 as an early pass over `plan.md`), O7 (one code path: a design line for size L), O9 (`rtk proxy` when output is parsed: one line in the global block), the E3 bug fix of O8. Drop: O2 `watch --budget-min` script, O5 plan grounding gate, O6 per-slice bookkeeping (replaced by rule 16), the verify and timeout script work of O8 (a config line instead), O10 retro metrics, O11 beyond one LS line.

| Step | Owns | Executor | Estimate |
|---|---|---|---|
| K1 text | `global/CLAUDE.md`, `rules/core.md` (new), `rules/archive/` (moved by `git mv`), `rules/README.md`, `kit/CLAUDE.md`, `kit/AGENTS.md`, constitution template, `kit/docs/code-structure.md`, prd-flow `SKILL.md`, `reference/*.md`, agent files, `MAINTAINING.md` M09, `CHANGELOG.md`, `plan-right-sized-deliveries.md` status line | A, worktree A | 60 min |
| K2 deletions | `ratchet.py`, allowlist template, `gate.py` and the `gate_*.py` modules listed in section 5, `commit_trailers.py`, `gates.sh` targets, CI trailer job, `guard_hook.py` narrowing, `verify.py` E3 fix, `stacks/*` timeout lines, and the kit tests that covered what was deleted (deleted with it) | B, worktree B | 60 min |
| Review | combined diff against sections 4 to 6 item by item | one reviewer | 20 min |
| Kit PR | push, PR to `main` (on the owner's request) | main thread | 5 min |
| Rollout 1 | clara-ai: `/ai-kit update`, `test_architecture.py`, allowlist, code-structure doc, PRD marker cleanup, `pyproject.toml` | A, worktree from `staging` | 45 min |
| Rollout 2 | agora-consulta-fe then modulo-integrador: `/ai-kit update`, `CLAUDE.md`, `AGENTS.md`, allowlist, eslint and test runner config | B, one worktree per repository from `staging` | 50 min |
| Check | `gates.sh lint` and `ratchet` once per repository; full suite once per repository against its baseline, in the background | main thread | 20 min |

Total about 2 h 40 min of wall clock with 2 executors. Brake: stop and report at 4 hours. Cut if needed: the clara-ai PRD marker cleanup and the FE Storybook plugin change move to a later PR. Measured after rollout (M07): docs-gate failure rate, share of edits outside product code and tests, cold starts per delivery, wall clock per delivery, against run 013.

# Plan: rule as data, one commit (kit and rollout to 3 repos)

Evidence: `eval/audit-2026-10-14-session-slowness/` (FINDINGS F01-F12, D01-D06, first A/B) and `.claude/skills/docs-flow-eval/results/` (v2 and v3 rounds). Branch `feat/docs-flow-eval`.

**Goal:** a rule change touches the PRD rows, code and tests in one commit, with no docs agent, no promote and no bookkeeping gate. The proof is the eval: at most the cost of v2 or v3 and 5/5 blind readers.
**Artifact:** the kit change on this branch, then one branch per repository (agora-consulta-fe, clara-ai, modulo-integrador) via `/ai-kit update`. Local commits only, no push.
**Out of scope:** reviews beyond one per delivery (already in), trimming the clara-ai PRD (831 KB) and TRD (a later delivery), the slow clara-ai test suite, product code.

## Target structure

| ID | Change | Replaces | Evidence |
|---|---|---|---|
| S1 | The approved rows go into the PRD in the commit of the task that implements them. No `pending code` or `planned` markers, no `Planned` TRD section, no promote for S and M sizes | DS09, DS17, DS18, promote.py on S/M | D02, D03, A/B: A1 and A2 left "(today: 60 s)" after promote |
| S2 | The commit body is the record: `Request:`, `Decided: <n><x> ... (rejected: ...)`, `Assumed:` in words, `Red:`, then `Rules:`. CHANGELOG.md is frozen (kept, never appended); `decisions.md` only for size L. A script prints a rule's history from git (`gate.py --history <ID>`) | DS12, G7, decisions.md on S/M | v2 readers 5/5; E1 |
| S3 | The INDEX IDs column is generated (`gen_index.py`, run by `gate.py --fix` and checked by the gate) | G2 by hand | D02 (G2 among the top failures) |
| S4 | HTML only in `/docs-html`; no HTML code in any other gate | G5, G29 and G32 outside docs-html | D02 (G5 and G29 were top failures) |
| S5 | The TRD names files and symbols, never a rule value (it cites the ID). The old-value Grep covers all of `docs/` and open change folders | DS33 (extended) | B2 stale TRD; E2 |
| S6 | The change gate has 6 errors: unique IDs (G1), complete row (G3), cited ID exists (G8, G15), changed rule has a test (G12), no em dash added (G4), INDEX current. TRD paths (G23, G24) and sibling drift (G28) become warnings or their own command | DS24, DS26 | 36% gate failure rate; G28 out-of-scope drift in every A run |
| S7 | Implementation is always dispatched to the dedicated executor agent, never `general-purpose` | (enforce DP prompt row) | v3: start context 57k to 24k, -38% tokens |
| S8 | Surveyor: no base lint or setup in `light` and `full`; it never rereads its own `sweep.md`; the sheet's "Becomes" column is the exact row text | survey.md steps | E3 (54 s lint, 33 KB reread) |
| S9 | Baseline and compare: strip ANSI before the summary match; the suite copy goes to `<repo>/.ai-kit/tmp`, not `%TEMP%` (8.3 path breaks vite on `[x]` and `(x)` folders) | new_failures.has_summary, baseline.py | first A/B: every baseline failed twice |
| S10 | Size L keeps `plan.md` (waves) and `decisions.md`; rows still land with the code task that implements them | write.md modes | A2: T01 and T02 split a type across executors |
| S11 | `docs-flow-eval` ships in the kit (skill, two agents, scenario format) and M07 points to it | MAINTAINING M07 | user request |

## Tasks (one owner each; files disjoint inside a wave)

| Task | Wave | Owns | Proves (test first) |
|---|---|---|---|
| T1 gate | 1 | `kit/.claude/skills/prd-flow/scripts/gate*.py`, new `gen_index.py`, `--history`, `--fix` | tests for S3, S4, S6 and `--history` on a fixture repo; removed checks no longer fire |
| T2 flow text | 1 | `prd-flow/SKILL.md`, `reference/*.md`, `kit/.claude/agents/prd-flow-*.md` | `test_runtime_consistency` style checks that no reference names promote, Planned, CHANGELOG append or a docs `apply` for S/M |
| T3 rules and templates | 1 | `rules/06-docs-system.md`, `rules/07-workflow.md`, `kit/.specify/memory/constitution.md`, `kit/CLAUDE.md`, `kit/AGENTS.md`, `kit/docs/templates/*`, `MAINTAINING.md` | DS rows renumbered as amendments, with no deleted IDs (DS06 applies to kit rules too) |
| T4 baseline | 1 | `kit/scripts/new_failures.py`, `kit/scripts/baseline.py` and its temp handling, tests | an ANSI-colored vitest summary parses; the suite copy path has no `~` |
| T5 retire | 2 | `promote.py` (kept only for L and for frozen markers), `state_record.py`, the kit tests that pin removed wording (about 51 files cite promote, CHANGELOG, decisions or Planned) | the suite is green with the removed behavior gone; a list of deleted or rewritten tests with the reason |
| T6 eval in kit | 2 | `.claude/skills/docs-flow-eval/*` (arm `current-prd-flow` rewritten for the new flow), `installer` hook if needed | the eval runs the new flow end to end on reconnect-window-90 |
| Eval | after 2 | the chief runs `/docs-flow-eval reconnect-window-90 current-prd-flow:2` | acceptance: executor time at most 7 min, readers 5/5, 0 docs gate failures |
| T7 FE | 3 | worktree `chore/ai-kit-rule-as-data`: `/ai-kit update`, constitution V amended, CLAUDE.md and AGENTS.md lines on PRD-first, CHANGELOG frozen note, open `changes/003` left as is | `gates.sh docs`, ratchet, lint green |
| T8 clara-ai | 3 | same, plus its pt-BR prd-gate skill if still present (adopt or leave with a note) | same |
| T9 BE | 3 | same for modulo-integrador | same |
| Review | end | one reviewer over the combined diff of the four repositories | |
| Suites | end | the kit suite and each repo's full suite once, against the recorded baselines | |

## Decided 2026-10-14 (user)

Scope approved; execution in a fresh session, wave by wave, from this file. D1 freeze the CHANGELOG. D2 amendment text: "Rule changes land in the PRD in the same commit as the code that implements them; the commit body records the request and the decision." D3 yes, size L keeps plan.md and decisions.md. D4 yes, existing `pending code` markers stay; no new change adds one.

## Decisions for the user (asked)

| # | Question | Recommendation |
|---|---|---|
| D1 | CHANGELOG.md: freeze (kept, never appended, history from git) or delete | Freeze: no history is lost and no reader breaks |
| D2 | Constitution amendment text in each repo (FE principle V says docs update "before the code") | "Rule changes land in the PRD in the same commit as the code that implements them" |
| D3 | Size L (new PRD or cross-section amendment) keeps plan.md and decisions.md | Yes |
| D4 | Rules pending code today (`pending code` markers already in the PRDs) | Keep them as they are; new changes never add one |

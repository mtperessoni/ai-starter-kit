# Rule catalog

Every rule of the kit, by domain. Each file is one table: `| ID | Rule | Why | Lands in |`. "Lands in" names the file of the target repository (or the skill section) that enforces the rule after `/ai-kit install`, so the catalog doubles as the checklist that nothing was lost.

Read only the file of the domain you need. IDs are stable: a new rule takes the next free number of its prefix.

| File | Prefix | Domain |
|---|---|---|
| [01-context-economy.md](01-context-economy.md) | CE | Token efficiency, lazy loading, budgets |
| [02-subagents.md](02-subagents.md) | SA | Orchestrator and workers, contracts, file-based handoff, caps, models, waves |
| [03-review.md](03-review.md) | RV | Code review with a ceiling of rounds |
| [04-testing.md](04-testing.md) | TS | Test-first, related tests only, full suite once, baseline, offline gates, containers and disk |
| [05-code-structure.md](05-code-structure.md) | AR, CX | AI-readable code layout, size limits, the ratchet, code constraints |
| [06-docs-system.md](06-docs-system.md) | DS | PRD by section, rule rows and Example column, CHANGELOG, TRD by feature, budget and checks, invariants, generated HTML, gate |
| [07-workflow.md](07-workflow.md) | WF | Cases C0 to C6, survey and sweeps, the decision sheet and its answers, PRD then TRD then plan then code, R09, commits and trailers |
| [08-writing-style.md](08-writing-style.md) | WS | Language, punctuation, comments, commits, tables |
| [09-lessons.md](09-lessons.md) | LS | What was measured and why each rule exists |
| [10-creation-and-install.md](10-creation-and-install.md) | PC, IN | Creating the PRD and TRD; installing and updating the kit per project |
| [11-telemetry.md](11-telemetry.md) | TM | Run telemetry: hooks, probes, the retro at the end of a delivery, thresholds |

## Where the rules end up

| Target file | Holds |
|---|---|
| `~/.claude/CLAUDE.md` | The global block: SA, RV, TS and WS rules that hold in any repository ([global/CLAUDE.md](../global/CLAUDE.md), installed by `install.sh`) |
| `CLAUDE.md` | Constitution index, the gate rule (WF01), code structure summary |
| `AGENTS.md` | Commands, critical constraints (CX), disk and container hygiene (TS27, TS29, TS33, TS34), directory map, finding things (CE), handing work to a subagent (SA04) |
| `changes/`, `changes/archive/` | WF26 to WF29, WF34: change folders (brief, design, plan) and their archive; project-owned, never touched by update |
| `.specify/memory/constitution.md` | Binding principles, domain specific plus the process principles of the kit |
| `docs/code-structure.md` | AR01 to AR28 |
| `docs/ai-readiness.md` | The readiness checklist by category, citing rule IDs (PC11, IN13) |
| `.ignore` | CE22, AR28: generated and vendored paths excluded from search |
| `.claude/settings.json` | CE22, IN11: gate allow list, read deny for generated and vendored paths |
| `scripts/hotspots.py`, `scripts/contract_drift.py` | PC12; DS30 |
| `docs/prd/`, `docs/trd/`, `docs/flow.md`, `docs/adr/` | DS rules applied |
| `.claude/skills/prd-create/`, `trd-create/` | PC rules: how the PRD and TRD are first written |
| `.claude/skills/prd-flow/` | WF, SA, RV, TS rules as operating procedure, plus `repo.md` (formerly `prd-gate`; WF35, IN14) |
| `.claude/skills/adr/` | DS23, DS27, DS28 |
| `.claude/agents/<risk>-reviewer.md` | RV12 to RV16 |
| `scripts/` and `ai-kit.json` | AR rules marked "ratchet", TS02 to TS08, TS22, TS28 to TS31, TS35, TS43 to TS54 (`docker_hygiene.py`, `clean_task_outputs.py`, `baseline.py`, `config_get.py`, the `docker` section, `tests.baseline_deselect`, `tests.always`) |
| `scripts/cleanup.py`, `scripts/watch.py` (via `gates.sh cleanup`, `gates.sh watch`) | SA58 (every run starts and ends with cleanup; `close` runs it last; a `SessionEnd` hook runs `cleanup --session-end`), SA59 (per-wave watch), TS34 |
| `scripts/guard_hook.py`, `reap.py`, `next_change_number.py`, `settings_check.py` | SA56 (the guard hook, registered in `settings.json` for every subagent, L12), SA57 (`gates.sh reap`); IN19 (doctor checks, change number reservation) |
| `ai-kit.allowlist.json` | The shrink-only ratchet allowlist, moved out of `ai-kit.json` (L15; WF31, IN20); `kit_config.py` reads it first |
| `.claude/settings.json`, `.ai-kit/runs/` | TM03, TM12, IN21: the telemetry hooks and the guard hook for every subagent (project-owned, merged; interpreter placeholder filled at install, L16) and the git-ignored run artifacts (SA51 and SA53 are enforced for subagents by `guard_hook.py`, L12) |
| `scripts/telemetry_hook.py`, `run_probe.py`, `retro.py` and the `telemetry` section of `ai-kit.json` | TM01 to TM11, TM13 to TM17 |
| `.claude/skills/prd-flow/scripts/gate.py` and its `gate_*.py` modules | WF31 to WF33 (`--trace`, `--change`, `--final`); WF43, WF44 (`--rules`: Q2, Q3, Q5 read from the CHANGELOG entry); WF68 to WF74 (sheet lint, `--plan` alignment, `--snapshot`, `--final --change`); DS34, DS37, DS39 (`--status`, `--trd`, `--sibling`); DS46 (`--docs`); CE29 (the record set) |
| `.claude/skills/prd-flow/scripts/prd_sweep.py` | WF38, WF39, WF41, WF50, WF57, WF83 (`gates.sh prd-sweep`: the surveyor's collecting half) |
| `.claude/skills/prd-flow/reference/` | Five files (L18): `dispatch.md` (WF65, WF67, WF71, WF76 to WF79, WF81, SA48, SA50, SA54, SA55, SA57, SA59; labels DP01 to DP13), `survey.md` (WF03 to WF07, WF10 to WF13, WF38 to WF41, WF57, WF59, WF83), `sheet.md` (WF15, WF43, WF47, WF68, WF69), `write.md` (WF21, WF26 to WF28, WF37, WF44, WF47, WF60, WF61, WF74; the TRD Planned rules TP01 to TP07 map to WF69, WF70), `run.md` (SA07, SA15, RV01 to RV10, V01 to V10, WF46); the old file to new heading map is `proposals/lite-reference-map.md` |
| `.claude/skills/prd-flow/scripts/build_prd_html.py`, `build_trd_html.py` | DS42: the generated `prd.html` and `trd.html`, checked by G29 and G32 |
| `.claude/skills/docs-html/` | DS45: the only place that builds the pages |
| `.github/CODEOWNERS` | WF48, DS43 |
| `scripts/commit_trailers.py` | WF49 (`gates.sh trailers`) |
| `.github/workflows/` | TS20, TS23 to TS26, RV17, CX10 |
| `.ai-kit/manifest.json` and the `/ai-kit` skill | IN rules |

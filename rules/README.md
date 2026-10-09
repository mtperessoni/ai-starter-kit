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
| [07-workflow.md](07-workflow.md) | WF | Cases C0 to C6, survey and sweeps, interview record, PRD then TRD then plan then code, R09, commits and trailers |
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
| `scripts/` and `ai-kit.json` | AR rules marked "ratchet", TS02 to TS08, TS22, TS28 to TS31, TS35, TS43 to TS53 (`docker_hygiene.py`, `clean_task_outputs.py`, `baseline.py`, `config_get.py`, the `docker` section, `tests.baseline_deselect`, `tests.always`) |
| `.claude/settings.json`, `.ai-kit/runs/` | TM03, TM12: the telemetry hooks (project-owned, merged) and the git-ignored run artifacts (SA51 and SA53 are behavior guidance in the agent files, no guard hook) |
| `scripts/telemetry_hook.py`, `run_probe.py`, `retro.py` and the `telemetry` section of `ai-kit.json` | TM01 to TM11, TM13 to TM16 |
| `.claude/skills/prd-flow/scripts/gate.py` and its `gate_*.py` modules, `state_record.py` | WF31 to WF33 (`--trace`, `--change`, `--final`); WF43, WF44 (`--rules`, `--applied`); WF68 to WF74 (`--questions`, `--plan` alignment, `--snapshot`, `--final --change`); DS34, DS37, DS39 (`--status`, `--trd`, `--sibling`); DS46 (`--docs`); CE29 (the state record) |
| `.claude/skills/prd-flow/reference/dispatch.md` | WF65, WF67, WF71, SA48, SA50, SA54, SA55 (labels DP01 to DP13); trd-planned.md TP06, TP07 map to WF69, WF70 |
| `.claude/skills/prd-flow/scripts/build_prd_html.py`, `build_trd_html.py` | DS42: the generated `prd.html` and `trd.html`, checked by G29 and G32 |
| `.claude/skills/docs-html/` | DS45: the only place that builds the pages |
| `.github/CODEOWNERS` | WF48, DS43 |
| `scripts/commit_trailers.py` | WF49 (`gates.sh trailers`) |
| `.github/workflows/` | TS20, TS23 to TS26, RV17, CX10 |
| `.ai-kit/manifest.json` and the `/ai-kit` skill | IN rules |

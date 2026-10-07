# Changelog

User-visible changes to the kit, newest first. Projects receive them through `/ai-kit update`.

## prd-flow v4

The `prd-gate` skill is now `prd-flow`, and the rule-change flow checks conflicts, gaps and the interview itself instead of trusting the conversation. Rules: WF35 to WF52, DS32 to DS43, PC13, PC14, IN14 to IN16, TM13 ([rules/](rules/README.md)).

Migration: `/ai-kit update` moves `prd-gate` to `prd-flow` (shows the list first; moves your `repo.md` and the state folder; replaces the old name in the files the kit manages). Hand-made `prd.html` files keep working (`html_mode: hand`) until you accept the generated version after a preview.

On update: move `.claude/skills/prd-gate/repo.md` to `.claude/skills/prd-flow/repo.md`, delete `.claude/skills/prd-gate/`, move `.claude/prd-gate/state/` to `.claude/prd-flow/state/`, replace `prd-gate` with `prd-flow` in CLAUDE.md, AGENTS.md, the constitution, `.claude/settings.json`, `.gitignore`, `ai-kit.json` and `docs/prd/README.md`, and add the new `repo.md` sections (Rule owners, Shared PRDs) and Gate config keys.

Workflow
- C0 only when `docs/prd/INDEX.md` does not exist; a new product, module or incoming spec in a repository with PRDs is a C5 of size L, swept against every existing PRD.
- Rules that come only from documents are `*(proposed)*` and go through confrontation and interview before they count; `--final` fails on a leftover one.
- New sweeps: K11 (rules in other sections that interact, found by meaning, with `Checked:` and `Conflicts:`), K12 (history of the rule in the CHANGELOG), K13 (rule owner and shared PRD), and remote branches for ID and change-number collisions.
- Assumed defaults are shown to the person in one block and confirmed; dimensions are `doc`, `assumed`, `open` or `n/a`.
- The PRD is confirmed (rule diff plus a summary of the non-table changes) before the TRD is written.
- R09: any behavior not covered by the approved rules, from anyone, goes through the short C5 before code. Ceilings of agents have one home (V08).
- `decisions.md` per change records the trade-offs decided and the alternatives rejected; rule owners are named when a change touches their section; commits carry `Rules:` or `Case: none (...)`.
- C1 answers say whether each rule is verified in code.

Gate
- `--rules` fails Q3 when the interview record is not closed; `--rules --applied` fails Q4 when the PRD differs from the approved rows.
- `--trd` (G23 to G26: cited paths and symbols exist, IDs match, size budget), `--status` (state per rule), `--sibling` (G28, shared PRDs identical), G27 (remote collisions), G30 (proposed rule left at `--final`).
- `gate.py` is split into modules named after their responsibility; `repo.md` Gate config gains `proposed_marker`, `html_mode`, `html_template`, `trd_budget_lines`, each with a default.

PRD and TRD formats
- Optional `Example` column in rule tables (`<given> → <expected outcome>`).
- TRD "Planned" is a slim table (file, changes or creates, symbols, IDs) with no values; the TRD has no History section; large TRD files split into parts; amendments are folded into their sections on promotion.

HTML
- `prd.html` is generated from the markdown by `build_prd_html.py` (tabs, toc, callouts, Example column, diagrams, decisions tab, light and dark, phone width); G29 fails when it is out of date.

Scripts
- `scripts/commit_trailers.py` and `gates.sh trailers`, run in CI on pull requests; the ratchet counts invariant gaps (`allowlist.invariant_gaps`, shrink-only); the retro reports the most-read docs (`doc_reads`); a CODEOWNERS template owns `docs/prd/**` by the rule owners.

Installer
- Update migrates `prd-gate` to `prd-flow` and, after a preview, a hand-made HTML to the generated one; install fills CODEOWNERS and proposes contract snapshots when a sibling consumer is listed.

Eval
- Scenarios S5 to S7 (conflict in another section, incoming spec, unanswered dimension) and `eval/arms-flow.json` compare the old and the new skill on the same runs, with the metrics `conflict_found`, `contradiction_left` and `gap_recorded`.

## Unreleased

Adoption in an existing repository: the kit installs without losing the project's docs language, TRD heading, gates script or structural test.

- prd-gate repo.md Gate config: `language` (default English) for the PRD, TRD, interview and gate output, read by R03 and `reference/workers.md`; `planned_heading` (default `Planned`) read by G8 and G20.
- `scripts/gates.sh` delegates to `scripts/gates.project.sh` when it exists: targets the kit does not define, and targets in `ai-kit.json` `commands.project_targets` (default `[]`), run there with their arguments.
- `scripts/ratchet.py`: `ai-kit.json` `ratchet.skip` (default `[]`) names checks to skip (`long_modules`, `long_tests`, `banned_names` or its alias `generic_names`, and the others `--init` prints); install.md says to skip the checks a project's own structural test already covers.
- prd-gate `reference/impact.md`: rows K01, K05 and K06 restored (K06 pointed at K01's text).
- prd-gate G3: the Source and Change via checks apply only to tables whose last header column is "Change via", so open-question tables no longer warn once per row.
- prd-gate G6: text inside markdown code spans (for example `<fileKey>`) is no longer stripped as an HTML tag, so it matches the escaped placeholder in the HTML.
- `docs/templates/prd.html`: explicit grid tracks (`minmax(0,1fr)`), so wide tables, mermaid diagrams and long tokens wrap or scroll inside their box and the page never exceeds 100% width.
- On update: add `language` and `planned_heading` to the `repo.md` Gate config table, filled from the project's existing docs (language of the prose, the TRD heading in use) and not from the defaults when they differ; add `commands.project_targets: []` and `ratchet: {"skip": []}` to `ai-kit.json`; copy `scripts/gates.sh` and `scripts/ratchet.py`; when the project has its own gates script or structural test, rename it to `scripts/gates.project.sh` and list its targets in `project_targets`, or list the overlapping checks in `ratchet.skip`; copy `docs/templates/prd.html` into the project's `prd.html` only by proposing the CSS diff.

Run telemetry: every run leaves summarized artifacts and a retrospective names what was slow, expensive, looping or wasteful.

- Hooks record tool calls, subagents, compactions and waits to `.ai-kit/runs/<context>/` (git-ignored); `gates.sh` test and build targets go through `run_probe.py` for time, memory and disk; `gates.sh retro` writes `retro.md` with findings only past the thresholds of `ai-kit.json` `telemetry`.
- prd-gate: step 1 runs `gates.sh context <slug>`; E20 runs the retro after the full suite and the final report lists the findings or says the run stayed within every threshold.
- Rules TM01 to TM12 in `rules/11-telemetry.md`.
- On update: copy `scripts/telemetry_hook.py`, `scripts/run_probe.py` and `scripts/retro.py`; merge the kit's hooks into `.claude/settings.json` keeping the project's own; add the `telemetry` section to `ai-kit.json` with the defaults; add `.ai-kit/runs/` to `.gitignore`.

AI readiness in any layout and any language: feature folders become a recommendation, every other technique applies to any folder structure (layers, legacy code, modules, mixes or anything else), and the kit gains the readiness techniques it was missing.

- Layout declared in `ai-kit.json`: `layout`, `areas` (product area to globs), `map_dirs` (folders that carry a `CLAUDE.md`), additive with `feature_root`. The ratchet checks IDs on area files and maps on map folders, and fails on an area or map folder that points nowhere. Configs without the new keys behave as before.
- Rules AR01, AR02 to AR07, AR10, AR11, AR13, AR19, DS15, TS16, PC09, CE07 rewritten layout and language agnostic; new AR20 to AR28 (layout optional, extract on touch, greppable wiring, crowded folders, complexity, dead code, duplicates, gradual typing, generated files), TS37 to TS42 (time budget, flaky list, snapshots, parallel-safe tests, builders, characterization tests), CE22 (search noise), DS30 (schema and contract snapshots), DS31 (pattern to copy), PC11, PC12, IN11 to IN13. MAINTAINING M06: every rule has a text-level part, a recipe part and review as fallback.
- `related_tests.py`: mirror names from `tests.mirror_patterns` (`OrderServiceTest`, `order.service.spec` and the like), `tests.match_symbol` for languages whose imports name namespaces or autoload, namespaced imports with backslashes, wall time against `tests.related_budget_seconds`, slowest tests from `tests.junit_xml`, a warning when snapshot files change.
- `ratchet.py`: `crowded_dirs` (`limits.files_per_dir`) and `generated_without_marker` (`generated_patterns`); generated files skip the other checks. `new_failures.py` lists `tests.flaky` failures without counting them.
- New `scripts/hotspots.py` and `scripts/contract_drift.py`; `gates.sh` gains `setup`, `hotspots`, `contracts`.
- trd-create: N4 is now the incremental readiness plan (`reference/readiness.md`) in the current layout; the move to feature folders is N5, optional. New `docs/ai-readiness.md` checklist and `docs/templates/folder-CLAUDE.md`. Install detects the layout, asks where a new area goes, writes `.ignore` and `.claude/settings.json` (the kit's `.claude/settings.json` now carries the gate permissions next to the telemetry hooks); doctor reports readiness per area.
- Every stack recipe gains Layout, Test naming, Generated files, Framework exemptions, Snapshots, Contracts and Setup, plus the linter rules for AR22 and AR24 to AR27.
- Candidates, not rules: a formatting PostToolUse hook, path-scoped rules, a language server for navigation; each to be measured in `eval/`.
- On update: add the new `ai-kit.json` keys with their defaults (`layout`, `areas`, `map_dirs`, `generated_patterns`, `contracts`, `limits.files_per_dir`, `commands.setup`, the new `tests` keys, the `crowded_dirs` and `generated_without_marker` allowlists seeded by `python scripts/ratchet.py --init`); when `feature_root` points at the whole source folder of a layer codebase, propose `layout`, `areas` and `map_dirs` instead and re-run `--init`; copy the new scripts, templates and `docs/ai-readiness.md`; propose `.ignore`, `.claude/settings.json`, the "This repository's layout" section of `docs/code-structure.md` and the new AGENTS.md lines as a diff; fill the recipe's new sections.

Living truth plus change deltas: every fact has one living home; a change folder holds intent, plan and state, never truth.

- The kit no longer depends on spec-kit: `/speckit-*` and `specs/` are gone from CLAUDE.md, AGENTS.md, the constitution, the skills and the rule catalog.
- Change folders `changes/NNN-<slug>/` by size (S, M, L) with `brief.md`, `design.md` and `plan.md`; finished ones are archived to `changes/archive/`.
- Order of authority: constitution, PRD, TRD, code; an active plan governs only the order of work.
- The plan's `Constitution check` replaces spec-kit's Constitution Check and Complexity Tracking.
- Rules WF26 rewritten, WF27 to WF34 added; IN10 added.
- `gate.py` gains `--trace` (every rule cited by a test, shrink-only allowlist), `--change` (brief IDs exist, P1 slices owned by a task) and `--final` (no `planned` leftovers on the base branch, run by CI on pushes to it).
- Fix: `gate.py` G5 compared an absolute HTML path with repo-relative diff paths and fired on every PRD table change; G10 compared the header row of a new table with the HTML. Agents had been patching the gate by hand in 3 of 8 evaluation runs.
- `eval/`: an unattended evaluation that compares flows on a small and a large synthetic service (hidden tests, PRD fidelity judge, blind code review, tokens, subagents, errors, time, reviews), with the decision rule in `eval/README.md`.
- On update: create `changes/archive/` (with a `.gitkeep`); leave a legacy `specs/` untouched as history; add `untested_rules` to the `allowlist` of `ai-kit.json`, seeded by `gate.py --trace` so today's untested rules are listed and shrink-only; propose the new sections of AGENTS.md (Directory map, Workflow, order of authority), CLAUDE.md (Constitution intro) and the constitution (Development Workflow step 2, Governance, header comment) as a diff; fill the repo.md "Spec-kit" and "Legacy specs" lines.

Container and disk hygiene, after a day of agent work filled a Windows disk (tens of GB of background task output, a 49.5 GB Docker disk file with 19 GB in use) and a first fix still leaked.

- `scripts/docker_hygiene.py` and `scripts/clean_task_outputs.py`; `gates.sh` gains `build`, `guard`, `sweep`, `docker-clean`, `clean-outputs`. `integration`, `full` and `build` refuse on low disk or over the image caps, and clean up from an `EXIT` trap, so a failed or interrupted run cleans up too.
- The sweep removes test-labelled containers, volumes and networks older than `DOCKER_STALE_MINUTES`, so a run killed before its teardown is cleaned by the next one, and a run still going in another session keeps its stack.
- The build cache is bounded by size (`--max-used-space`), never by age: `--filter until=24h` kept everything built that day, and `--keep-storage` is now a floor, not a ceiling.
- A cap over all images (`TOTAL_IMAGE_CAP_GB`) catches third-party pulls; a warning names the Docker Desktop disk file when it passes `DOCKER_DISK_WARN_GB`, with how to compact it.
- Labels come from a new optional `docker` section of `ai-kit.json`; without it every Docker target does nothing.
- Rules TS27 to TS36; AGENTS.md "Disk and container hygiene"; testing template "Containers"; the Python recipe's "Containers" section; the global block's "Docker and disk"; install detects Docker and doctor reports drift.
- On update: copy the two scripts and `gates.sh`; when the project uses Docker, add the `docker` section and wire the recipe's "Containers" section (labels, `purpose` from the environment, session sweep, guards before builds, failing teardown); propose the AGENTS.md section and the testing.md rows as a diff; refresh the global block.

## 2026-10-04

First release, extracted from the production AI service where the rules were built and measured.

- `/ai-kit` installer with install, update and doctor modes; `install.sh` and `install.ps1` for the global skill and block.
- Skills `prd-create`, `trd-create`, `prd-gate` and `adr`.
- Docs system: PRD by section with rule rows and an HTML reading version, TRD by feature, invariants, testing guide, end-to-end flow, ADRs, templates.
- Stack-free scripts: `gates.sh`, `ratchet.py`, `related_tests.py`, `new_failures.py`, `move_lines.py`, with end-to-end tests.
- Stack recipes for Python, Node, Go, JVM, .NET, Rust, Ruby and PHP, plus a generic path.
- CI with the offline gate, the docs gate, the ratchet, a secret scan and an automated Claude review.
- Rule catalog with every rule, its reason and where it lands.

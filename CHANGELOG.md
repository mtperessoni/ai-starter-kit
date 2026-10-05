# Changelog

User-visible changes to the kit, newest first. Projects receive them through `/ai-kit update`.

## Unreleased

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

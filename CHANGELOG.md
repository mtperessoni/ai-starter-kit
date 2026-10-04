# Changelog

User-visible changes to the kit, newest first. Projects receive them through `/ai-kit update`.

## Unreleased

Living truth plus change deltas: every fact has one living home; a change folder holds intent, plan and state, never truth.

- The kit no longer depends on spec-kit: `/speckit-*` and `specs/` are gone from CLAUDE.md, AGENTS.md, the constitution, the skills and the rule catalog.
- Change folders `changes/NNN-<slug>/` by size (S, M, L) with `brief.md`, `design.md` and `plan.md`; finished ones are archived to `changes/archive/`.
- Order of authority: constitution, PRD, TRD, code; an active plan governs only the order of work.
- The plan's `Constitution check` replaces spec-kit's Constitution Check and Complexity Tracking.
- Rules WF26 rewritten, WF27 to WF34 added; IN10 added.
- On update: create `changes/archive/` (with a `.gitkeep`); leave a legacy `specs/` untouched as history; add `untested_rules` to the `allowlist` of `ai-kit.json`, seeded by `gate.py --trace` so today's untested rules are listed and shrink-only; propose the new sections of AGENTS.md (Directory map, Workflow, order of authority), CLAUDE.md (Constitution intro) and the constitution (Development Workflow step 2, Governance, header comment) as a diff; fill the repo.md "Spec-kit" and "Legacy specs" lines.

## 2026-10-04

First release, extracted from the production AI service where the rules were built and measured.

- `/ai-kit` installer with install, update and doctor modes; `install.sh` and `install.ps1` for the global skill and block.
- Skills `prd-create`, `trd-create`, `prd-gate` and `adr`.
- Docs system: PRD by section with rule rows and an HTML reading version, TRD by feature, invariants, testing guide, end-to-end flow, ADRs, templates.
- Stack-free scripts: `gates.sh`, `ratchet.py`, `related_tests.py`, `new_failures.py`, `move_lines.py`, with end-to-end tests.
- Stack recipes for Python, Node, Go, JVM, .NET, Rust, Ruby and PHP, plus a generic path.
- CI with the offline gate, the docs gate, the ratchet, a secret scan and an automated Claude review.
- Rule catalog with every rule, its reason and where it lands.

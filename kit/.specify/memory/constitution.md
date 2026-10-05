<!--
Target path: .specify/memory/constitution.md (the path is kept for compatibility; spec-kit is optional).
Keep each principle short: a rule, the controls that enforce it, and the registered exceptions.
Principles marked [kit] come from the playbook and are recommended as-is; [domain] ones are yours.
-->

# <Project> Constitution

## Core Principles

### I. <Domain principle> (NON-NEGOTIABLE) [domain]
<The rule in two or three sentences. What it forbids. How it is enforced (test, reviewer, gate).>

### II. Test-First With Deterministic Doubles (NON-NEGOTIABLE) [kit]
Every behavior starts as a failing test. External services and models are replaced by deterministic fakes in the unit suite, which runs with no network and no database; the gate script sets that environment itself. Tests that need a real model or the network carry a marker and never gate a merge. While working, only related tests run; the full suite runs once per delivery against a recorded baseline.

### III. Documents Are the Source of Truth [kit]
Product behavior lives in `docs/prd/` as rule rows with permanent IDs; code maps live in `docs/trd/`, one per area. A rule change updates PRD and TRD, and is approved by a person, before any code. Every module and test cites the IDs it implements or proves. Superseded wording moves literally to the CHANGELOG.

### IV. AI-Readable Code [kit]
Code follows `docs/code-structure.md`: one area per PRD area (feature folders recommended, any declared layout), size limits, one responsibility per file with a unique descriptive name, composition over inheritance, explicit state. A structural ratchet enforces it and its allowlist only shrinks.

### V. Bounded Agent Work [kit]
Agents work against a contract and communicate through files; every agent has a ceiling of calls and time; code review has a ceiling of rounds per delivery; decisions that change behavior or weaken a safety control go back to a person.

### VI. <Domain principle: auditability, rollback, configuration as data, safety...> [domain]
<...>

### VII. Secrets and Trust Boundaries [kit]
No secret in source, prompt, config file or fixture. Configuration is typed and validated at boot; the service refuses to start when it is invalid.

## Technology Constraints
<Stack, persistence ownership, boundaries with other systems.>

## Development Workflow
1. **Gate first.** `/prd-gate` classifies every behavior change; a rule change goes PRD, TRD, plan, code.
2. **Change folder by size** before code: S none or `plan.md`; M `brief.md` and `plan.md`; L also `design.md`, all under `changes/NNN-<slug>/`. What is durable is promoted to the PRD, TRD or ADR and the folder is archived.
3. **Implement** test first, one commit per task.
4. **Gates.** Lint, type check, ratchet and the full offline suite pass before any merge. Coverage may not decrease.

Comments in code are the exception, not the rule: name things well and let the code speak.

Everything in this repository is written in English.

## Governance
This constitution supersedes any other convention in this repository.
- Every pull request verifies compliance. A violation is fixed or explicitly justified in the plan's `Constitution check` table.
- Amendments require a pull request that changes this file, states the rationale and updates any plan the change invalidates. Changing a protected rule requires an ADR in `docs/adr/`.
- Versioning is semantic: MAJOR for removing or redefining a principle, MINOR for a new principle or materially new rule, PATCH for wording.
- Runtime guidance for AI agents lives in `AGENTS.md`. When `AGENTS.md` and this constitution disagree, this constitution wins.

**Version**: 1.0.0 | **Ratified**: <YYYY-MM-DD> | **Last Amended**: <YYYY-MM-DD>

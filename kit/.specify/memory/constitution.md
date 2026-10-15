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
Product behavior lives in `docs/prd/` as rule rows with permanent IDs; code maps live in `docs/trd/`, one per area. A rule change is approved by a person. Rule changes land in the PRD in the same commit as the code that implements them; the commit body records the request and the decision. The TRD is updated once per delivery, in its last slice. `git log` is the history of a rule; the CHANGELOG is frozen.

### IV. AI-Readable Code [kit]
Code follows `docs/code-structure.md`: one area per PRD area (feature folders recommended, any declared layout), size limits, one responsibility per file with a descriptive name, composition over inheritance, explicit state. The stack linter enforces size, complexity and dependency direction against a file-list baseline; the ratchet only bans generic file names and checks generated markers.

### V. Bounded Delivery [kit]
A delivery is one vertical slice with an estimate agreed before it starts and a report at its end; defects ship as small fixes before any restructuring; the session that executes a slice writes its code, and a subagent works against a contract and hands back instead of growing; code review has a ceiling of rounds per delivery; decisions that change behavior or weaken a safety control go back to a person.

### VI. <Domain principle: auditability, rollback, configuration as data, safety...> [domain]
<...>

### VII. Secrets and Trust Boundaries [kit]
No secret in source, prompt, config file or fixture. Configuration is typed and validated at boot; the service refuses to start when it is invalid.

## Technology Constraints
<Stack, persistence ownership, boundaries with other systems.>

## Development Workflow
1. **Scope first.** Before the first edit of a delivery: the goal, what is out of scope and an estimate in minutes, agreed by the person. One delivery is one vertical slice with its own PR; size L writes one short plan, `changes/NNN-<slug>/plan.md`, S and M no plan files.
2. **Confirm, then land with the code.** A rule change is confirmed by the person; its PRD rows land in the commit that implements it. `/prd-flow` runs this gate only when a person explicitly types `/prd-flow`; an agent never starts it on its own.
3. **Test first.** A failing test first; before handing a slice back, its tests and the tests that import the files it touched; the full offline suite once per delivery against the baseline.
4. **Gates before merge.** Lint, type check and the full offline suite pass. Coverage may not decrease.

Comments in code are the exception, not the rule: name things well and let the code speak.

Language: `AGENTS.md` "Critical constraints" declares it once.

## Governance
This constitution supersedes any other convention in this repository.
- Every pull request verifies compliance. A violation is fixed or explicitly justified in the plan's `Constitution check` table.
- Amendments require a pull request that changes this file, states the rationale and updates any plan the change invalidates. Changing a protected rule requires an ADR in `docs/adr/`.
- Versioning is semantic: MAJOR for removing or redefining a principle, MINOR for a new principle or materially new rule, PATCH for wording.
- Runtime guidance for AI agents lives in `AGENTS.md`. When `AGENTS.md` and this constitution disagree, this constitution wins.

**Version**: 2.0.0 | **Ratified**: <YYYY-MM-DD> | **Last Amended**: <YYYY-MM-DD>

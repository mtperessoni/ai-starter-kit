# <project>: Claude Code bootstrap

> <One sentence: what this service or app is and who uses it.>

## Constitution

Binding, and it wins over everything else in this repository. Full text: `.specify/memory/constitution.md`. Read the whole principle your change touches before writing code; the plan's `Constitution check` and the reviewer agents read the file in full.

- **I. <Principle name> (NON-NEGOTIABLE).** <One line.>
- **II. Test-First With Deterministic Doubles (NON-NEGOTIABLE).** Failing test first, fakes for external services and models, the unit suite runs offline.
- **III. Documents Are the Source of Truth.** Behavior lives in `docs/prd/`, code maps in `docs/trd/`; a rule change updates them before the code.
- **IV. AI-Readable Code.** `docs/code-structure.md`, enforced by the ratchet and the linter rules.
- **V. Bounded Agent Work.** Contracts, ceilings and review rounds; behavior changes go back to a person.
- **VI. <Principle name>.** <One line.>
- **VII. Secrets and Trust Boundaries.** No secret in source, prompt, config file or fixture; configuration is typed and validated at boot.

## Product rules flow

Every change in this repository and every question about product behavior starts with `/prd-flow` (`.claude/skills/prd-flow/`). Two exceptions skip the gate: small changes (a typo, a log line, a rename, a one-line fix that changes no rule) and fixes to tests. A rule change never goes straight to code: PRD, then TRD, then plan, then code, and only after the person asking has seen the current rule, what would change, and confirmed it. Product changes run through prd-flow, whose main thread coordinates the agents (`.claude/agents/prd-flow-*`) and executes no task; the executor `close` mode promotes, commits and runs the closing gate.

## Code structure

All code follows `docs/code-structure.md` (rules AR01 to AR28); `scripts/gates.sh ratchet` and the linter rules behind `scripts/gates.sh lint` enforce it. The short version:

- **Where:** `<layout of this repository, filled at install>`; feature folders (`<src>/features/<f>/` per PRD area) are recommended, any declared layout works. Start a task by reading the area's map (`CLAUDE.md`) and its TRD in `docs/trd/`.
- **Size:** module up to 500 lines, function up to 80, class up to 300, test file up to 1,200. One responsibility per file, named after it and unique in the repo; never `helpers`, `utils`, `shared`, `common`, `misc`, `state`.
- **Shape:** composition over mixins; explicit state, no shared mutable closures; re-export only in an area's public entry.
- **Traceability:** every module of an area cites the PRD IDs it implements, every test the ID it proves; update the area's map and TRD in the same commit as the code.
- **Tests:** where the stack expects them, beside the code or its mirrored tree (AR10); mocks target the module of the caller. A person may run `scripts/gates.sh related`; a prd-flow executor runs only its own test plus `gates.sh fix-files` and `lint-files` on its files; the chief runs one `gates.sh verify` per wave; the full suite runs once, at the end of a delivery.
- **Processes:** long commands run in the background with an explicit timeout longer than the run; never kill processes by image name (`taskkill /IM`, `pkill`, `killall`), use `scripts/gates.sh reap`.
- **Returns:** every prd-flow agent returns at most 20 lines with the five fields `Status`, `Files:`, `Commit:`, `Route:`, `Next:`.
- **Moving code:** by script (line ranges or AST), never retyped.
- **Language:** everything in English: code, docs, PRD, TRD, artifacts, commits.

@AGENTS.md

# <project>: Claude Code bootstrap

> <One sentence: what this service or app is and who uses it.>

## Constitution

Binding, and it wins over everything else in this repository. Full text: `.specify/memory/constitution.md`. Read the whole principle your change touches before writing code; the plan's `Constitution check` and the reviewer agents read the file in full.

- **I. <Principle name> (NON-NEGOTIABLE).** <One line.>
- **II. Test-First With Deterministic Doubles (NON-NEGOTIABLE).** Failing test first, fakes for external services and models, the unit suite runs offline.
- **III. Documents Are the Source of Truth.** Behavior lives in `docs/prd/`, code maps in `docs/trd/`; rule changes land in the PRD in the same commit as the code that implements them; the TRD is updated once per delivery.
- **IV. AI-Readable Code.** `docs/code-structure.md`, enforced by the ratchet and the linter rules.
- **V. Bounded Delivery.** One vertical slice per delivery, with an estimate agreed first and a report at its end; review has a ceiling of rounds; behavior changes and safety nets go back to a person.
- **VI. <Principle name>.** <One line.>
- **VII. Secrets and Trust Boundaries.** No secret in source, prompt, config file or fixture; configuration is typed and validated at boot.

## Product rules flow

`/prd-flow` (`.claude/skills/prd-flow/`) runs only when the person explicitly types `/prd-flow`; never start it on your own, whatever the task. Without it, work directly and keep the documents true: a rule change is shown to the person (today's rule and what would change) and confirmed before the code; the PRD file that owns the rule changes in the commit that implements it, whose body says what was decided (`Decided:`) and ends with `Rules:`; the area's TRD is updated once, in the last slice of the delivery. When the person does run prd-flow, its main thread coordinates the agents (`.claude/agents/prd-flow-*`) and executes no task; the executor `close` mode commits and runs the closing gate.

## Code structure

All code follows `docs/code-structure.md` (rules AR01 to AR28); `scripts/gates.sh ratchet` and the linter rules behind `scripts/gates.sh lint` enforce it. The short version:

- **Where:** `<layout of this repository, filled at install>`; feature folders (`<src>/features/<f>/` per PRD area) are recommended, any declared layout works. Start a task by reading the area's map (`CLAUDE.md`) and its TRD in `docs/trd/`.
- **Size:** module up to 500 lines, function up to 80, class up to 300, test file up to 1,200. One responsibility per file, named after it and unique in the repo; never `helpers`, `utils`, `shared`, `common`, `misc`, `state`.
- **Shape:** composition over mixins; explicit state, no shared mutable closures; re-export only in an area's public entry.
- **Traceability:** every module of an area cites the PRD IDs it implements, every test the ID it proves; the area's map and TRD are updated once per delivery, in its last slice.
- **Tests:** where the stack expects them, beside the code or its mirrored tree (AR10); mocks target the module of the caller. Before handing back a slice, run `scripts/gates.sh related` on the files it touched (their tests and the tests that import them) plus `gates.sh fix-files` and `lint-files`; the full suite runs once, at the end of a delivery.
- **Processes:** a subagent runs long commands in the foreground with an explicit timeout under 600 s, output to a file; only the main thread starts background work, with a timeout longer than the run. Never kill processes by image name (`taskkill /IM`, `pkill`, `killall`): use `scripts/gates.sh reap`.
- **Returns:** a subagent returns at most 15 lines: done, files, tests, gaps, minutes used; prd-flow agents use their five fields (`.claude/skills/prd-flow/reference/run.md` "Every agent").
- **Moving code:** by script (line ranges or AST), never retyped.
- **Language:** everything in English: code, docs, PRD, TRD, artifacts, commits.

@AGENTS.md

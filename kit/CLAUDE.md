# <project>: Claude Code bootstrap

> <One sentence: what this service or app is and who uses it.>

## Constitution

Binding, and it wins over everything else in this repository. Full text: `.specify/memory/constitution.md`. Read the whole principle your change touches before writing code; the plan's `Constitution check` and the reviewer agents read the file in full.

- **I. <Principle name> (NON-NEGOTIABLE).** <One line.>
- **II. Test-First With Deterministic Doubles (NON-NEGOTIABLE).** Failing test first, fakes for external services and models, the unit suite runs offline.
- **III. Documents Are the Source of Truth.** Behavior lives in `docs/prd/`, code maps in `docs/trd/`.
- **IV. AI-Readable Code.** `docs/code-structure.md`, enforced by the linter rules; the ratchet only for generic names and generated markers.
- **V. Bounded Delivery.** One vertical slice per delivery, with an estimate agreed first and a report at its end; review has a ceiling of rounds; behavior changes and safety nets go back to a person.
- **VI. <Principle name>.** <One line.>
- **VII. Secrets and Trust Boundaries.** No secret in source, prompt, config file or fixture; configuration is typed and validated at boot.

## Product rules flow

`/prd-flow` (`.claude/skills/prd-flow/`) runs only when the person explicitly types `/prd-flow`; never start it on your own. Without it, work directly and keep the documents true as `AGENTS.md` "Workflow" says. When the person runs it, its main thread coordinates the agents (`.claude/agents/prd-flow-*`) and executes no task; the executor `close` mode commits and runs the closing gate.

@AGENTS.md

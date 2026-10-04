# Generic (no recipe matches)

When no recipe matches, or for an ecosystem not listed (Swift, Dart, Elixir, Scala, C and C++, infrastructure repositories), the installer builds the adaptation itself, in this order:

1. **Read what the project already runs.** CI files, `Makefile`, `justfile`, `Taskfile.yml`, scripts folders, the README "Development" section. The commands a team already runs win.
2. **Find the test runner** and how to run one file, how to exclude a slow or external tier, and what a failure line looks like (run the suite once into a log and read the summary to write `tests.failure_regex`).
3. **Find the linter and formatter** with a verify mode and a repair mode.
4. **Structure enforcement:** `scripts/ratchet.py` covers module and test size, names, PRD IDs in headers and feature maps for any text language. For function length and import direction, look up the ecosystem's linter rule (search "<language> max function length lint rule" and "<language> architecture dependency rules"); when none exists, record AR03 functions, AR04, AR05 and AR09 as "review" in `docs/code-structure.md` instead of "linter".
5. **Ask the user** only what remains: one AskUserQuestion with the commands found and a recommended choice for each gap.
6. **Verify** every command by running it before writing it into `ai-kit.json`.

Afterwards, propose a new recipe file for this kit (MAINTAINING.md "Adding a stack recipe") so the next project of this ecosystem installs without the research.

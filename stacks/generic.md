# Generic (no recipe matches)

When no recipe matches, or for an ecosystem not listed (Swift, Dart, Elixir, Scala, C and C++, infrastructure repositories), the installer builds the adaptation itself, in this order:

1. **Read what the project already runs.** CI files, `Makefile`, `justfile`, `Taskfile.yml`, scripts folders, the README "Development" section. The commands a team already runs win.
2. **Find the test runner** and how to run one file, how to exclude a slow or external tier, and what a failure line looks like (run the suite once into a log and read the summary to write `tests.failure_regex`).
3. **Find the linter and formatter** with a verify mode and a repair mode.
4. **Structure enforcement:** `scripts/ratchet.py` covers module and test size, names, PRD IDs in headers and feature maps for any text language. For function length and import direction, look up the ecosystem's linter rule (search "<language> max function length lint rule" and "<language> architecture dependency rules"); when none exists, record AR03 functions, AR04, AR05 and AR09 as "review" in `docs/code-structure.md` instead of "linter".
   The new rules fall back the same way: text-level part by `scripts/ratchet.py` and the scripts, a linter when the ecosystem has one, otherwise record "review" in `docs/code-structure.md`.

   | Rule | Fallback |
   |---|---|
   | AR22 runtime dispatch | grep for the language's reflection and dynamic call forms; linter rule if found, else review |
   | AR23 crowded folders, AR28 generated markers | `scripts/ratchet.py` (any language) |
   | AR24 complexity | a multi-language complexity CLI such as `lizard` (look up: supports many languages, flags `-C` for complexity, `-a` for parameters, `-L` for length); else the ecosystem's linter; else review |
   | AR25 dead code | the compiler or linter's unused warnings; else review plus DS13 |
   | AR26 duplicates | `jscpd` or PMD CPD (both multi-language); else review |
   | AR27 typing | the language's type checker in its strictest per-module mode; "not applicable" for statically typed languages |
5. **Declare the layout** (`layout`, `areas`, `map_dirs`), the test naming (`tests.mirror_patterns`, `tests.match_symbol`), `generated_patterns` with the generator's marker (the ratchet's default marker regex covers the usual headers; when the generator's header matches none, set `generated_marker`), `tests.snapshot_patterns` and the runner's update flag agents must not use, `contracts` (the schema or API snapshot the framework produces, or a dump command), `commands.setup`, and `tests.junit_xml` when the runner can write JUnit XML. Record any of these that cannot be found as "review" in `docs/code-structure.md`.
6. **Complete `code_extensions`** for the ecosystem so the ratchet sees every source file: for example `.vue`, `.svelte`, `.astro`, `.ex`, `.exs`, `.erl`, `.scala`, `.swift`, `.dart`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`, `.m`, `.lua`, `.zig`, `.tf` (infrastructure), `.sql`.
7. **Ask the user** only what remains: one AskUserQuestion with the commands found and a recommended choice for each gap.
8. **Verify** every command by running it before writing it into `ai-kit.json`.

Afterwards, propose a new recipe file for this kit (MAINTAINING.md "Adding a stack recipe") so the next project of this ecosystem installs without the research.

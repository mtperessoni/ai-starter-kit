# Code structure for AI

Single source of the rules for where and how code lives in this repository. They apply to people and agents, to all new code and every change.

Why: an agent finds code by name (Glob, Grep) and pays for each file and each hop it reads. Small files, one responsibility, a name that says what the file does and the PRD ID at the top let the agent read only what the task needs.

## Recommended tree
Feature folders are the recommended layout (AR20); any other layout works through "This repository's layout".
```
<src>/
  <entry>                 entry point
  app/                    route assembly and dependency wiring; injects features into the core
  features/<f>/           one folder per PRD area
    CLAUDE.md             folder map, auto-loaded by Claude Code
    <public entry>        the feature's public interface (__init__.py, index.ts)
    domain/               pure rules, no IO
    <responsibility>.<ext> services with IO, one per responsibility
    tests/                the feature's tests, beside the code
  infra/                  shared: persistence, providers, observability, config, auth
```
Features: <list>. Core features: <list>.

## This repository's layout
Filled at install from `ai-kit.json`; keep it equal to the config.

| Item | Value |
|---|---|
| Layout | `<one line on how code is organized here, in this project's words>` |
| Feature root | `<src>/features/` (every subfolder is an area and a map folder) |
| Map folders | `<folders with a CLAUDE.md besides the feature folders>` |
| Where a new area goes | `<default: a new folder under the feature root>` |
| Dependency direction | `<the direction that applies to this layout, as AR09 lists it>` |
| Tests location | `<beside the code in <area folder>/tests/, or the stack's mirrored tree>` |

| Area | Files or globs | Map folder |
|---|---|---|
| `<area>` | `<glob of its files, for code outside the feature root>` | `<folder with its CLAUDE.md>` |

## Rules
| ID | Rule | Checked by |
|---|---|---|
| AR01 | New code lives in the area of the PRD it implements. Recommended: one feature folder per PRD area; shared code used by three or more areas in `infra/`. Another layout is declared in `ai-kit.json` (`layout`, `areas`, `map_dirs`) and in the table above; code of an existing area stays in its files, a new area goes where the table says | review |
| AR02 | One responsibility per file; the file name states it and is unique in the repository. Forbidden: `helpers`, `utils`, `shared`, `common`, `misc`, `state`. `unique_name_exempt` holds the names the framework imposes | ratchet |
| AR03 | Limits: module up to 500 lines, function up to 80, class up to 300, test file up to 1,200. The recipe may adjust a limit for a verbose language, reason recorded here | ratchet (modules, tests), linter (functions, classes) |
| AR04 | Composition over mixins: a class receives small collaborators in its constructor, each readable alone. Never inherit from two in-repo classes; inheritance the framework requires is allowed | linter |
| AR05 | Explicit state: no `nonlocal` or closures sharing mutable state; a session's state is an object passed along. The framework's own state primitive counts as explicit | linter |
| AR06 | The PRD IDs a module implements go in its first comment, within `limits.id_header_lines`; every test cites the ID it proves. A Grep by ID finds rule, code and test. Checked for files of an area | ratchet |
| AR07 | Every map folder (feature folders plus `map_dirs`) has a `CLAUDE.md` of at most 20 lines: a feature folder gets the feature map, a folder holding several areas gets one row per area. Changing a piece changes the map in the same commit | ratchet (present, at most 20 lines), review (content) |
| AR08 | Re-export only in the area's public entry; importers use the defining module. The public entry has no side effects | review |
| AR09 | Dependency directions are declared for this repository in "This repository's layout". Examples: with feature folders, a feature uses `infra` and another feature only through its public entry, core features do not import peripheral ones, `infra` never imports a feature; with layers, upper layers use lower ones and never the reverse (for example entry, then services, then persistence); with modules, modules depend only through their public entry; any other structure declares its own directions there; no cycles in any structure (AR20) | linter |
| AR10 | Tests beside the code (`<area folder>/tests/`) when the stack allows, otherwise the stack's mirrored tree with the same relative path; named after the module with one of `tests.mirror_patterns`; harness with its own name; a test class imported by another file gets an alias starting with `_` where the collector would run it twice | review |
| AR11 | Mocks and monkeypatches target the module of the caller, not the definer nor a re-export. Where dependency injection is used the fake is injected and this does not apply | review |
| AR12 | Moving code is done by script (line ranges or AST), never retyped; the model decides the map and fixes imports | review |
| AR13 | The TRD is 1:1 with the areas: `docs/trd/<area>.md` maps the area's files wherever they live; an area over `trd_budget_lines` is a folder `docs/trd/<area>/` of parts mirroring the PRD section groups plus its `README.md`; the TRD has no History section; every map `CLAUDE.md` that covers the area links to it | review; `gate.py --trd` (paths, symbols, IDs, budget) |
| AR14 | Paths computed from the module's own location use its real depth; after moving, check them | review |
| AR19 | `scripts/ratchet.py` also checks crowded folders (AR23), generated markers (AR28) and the layout config: an area whose globs match no file or a `map_dirs` entry that does not exist fails, never allowlisted | ratchet |
| AR20 | The feature-folder layout is a recommendation, never a precondition. Every other rule applies in any layout and language; moving to feature folders is optional and incremental | review |
| AR21 | In a legacy area, a task that must change a file over the limits first extracts the responsibility it touches into a new module named after it (by script, AR12), then changes that module; it never grows the file | ratchet, review |
| AR22 | Greppable wiring: every call site names its target literally; no dispatch through names assembled at runtime; a dispatch table lists its targets by name. Wiring by framework convention is allowed when the area TRD "How it enters the flow" names the convention and the files it binds | review; linter where the recipe has one |
| AR23 | At most `limits.files_per_dir` code files directly in one folder, tests excluded; a crowded folder splits by area or responsibility | ratchet (`crowded_dirs`) |
| AR24 | Complexity: cyclomatic up to 10, nesting depth up to 4, parameters up to 5 per function | linter with baseline (recipe), review |
| AR25 | Dead code is deleted: unused modules, functions and exports fail the dead-code check with a shrink-only baseline; symbols reached only by reflection or DI go to the tool's allowlist | linter (recipe), review |
| AR26 | Duplicated blocks are detected with a shrink-only baseline; a fix inside a duplicated block fixes every copy or extracts it | linter (recipe), review |
| AR27 | With gradual or optional typing, strictness only goes up, per module, with a shrink-only baseline; boundaries and public functions are typed. Not applicable to statically typed languages | type checker (recipe) |
| AR28 | Generated files match `generated_patterns`, start with a generated marker in their first lines, are excluded from the other structure checks, from search and from agent reads; a change regenerates them, never edits them | ratchet (`generated_without_marker`) |

## How to check
- `scripts/gates.sh ratchet` is the ratchet: it fails when a "ratchet" rule is violated outside the allowlist, and the allowlist only shrinks.
- `scripts/gates.sh lint` runs the linter rules for function and class size, inheritance, complexity and import direction (configured per stack in `ai-kit.json`); `scripts/gates.sh imports` catches import cycles.
- `scripts/gates.sh hotspots` ranks files by recent commits times lines, to order legacy work.
- `scripts/gates.sh contracts` fails when a schema or contract snapshot drifted from its source.

## When creating something new
1. Find the area by the PRD ID (`docs/prd/INDEX.md`) and `docs/trd/README.md`, then read its map (the area's `CLAUDE.md` or its row in a folder map).
2. Create the module named after its responsibility, in the area's files, with the IDs in its first comment.
3. Write the test where AR10 says, citing the ID.
4. Update the map and the TRD in the same commit.
5. Run only the tests related to what you touched; the full suite runs once, at the end of the delivery.

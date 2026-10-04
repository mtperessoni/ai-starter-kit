# Code structure for AI

Single source of the rules for where and how code lives in this repository. They apply to people and agents, to all new code and every change.

Why: an agent finds code by name (Glob, Grep) and pays for each file and each hop it reads. Small files, one responsibility, a name that says what the file does and the PRD ID at the top let the agent read only what the task needs.

## Tree
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

## Rules
| ID | Rule | Checked by |
|---|---|---|
| AR01 | New code lives in the feature of the PRD area it implements; what three or more features use and is not product rule goes to `infra/` | review |
| AR02 | One responsibility per file; the file name states it and is unique in the repository. Forbidden: `helpers`, `utils`, `shared`, `common`, `misc`, `state` | ratchet |
| AR03 | Limits: module up to 500 lines, function up to 80, class up to 300, test file up to 1,200 | ratchet (modules, tests), linter (functions, classes) |
| AR04 | Composition over mixins: a class receives small collaborators in its constructor, each readable alone. Never inherit from two in-repo classes | linter |
| AR05 | Explicit state: no `nonlocal` or closures sharing mutable state; a session's state is an object passed along | linter |
| AR06 | Every feature module's docstring (or header) cites the PRD IDs it implements (`"""ORD-03, ORD-07: ..."""`); every test cites the ID it proves. A Grep by ID finds rule, code and test | ratchet |
| AR07 | Every feature has a `CLAUDE.md` of at most 20 lines: responsibility, PRD IDs with their file, entry point, pieces, what must not break, where the tests are, link to its TRD. Changing a piece changes the map in the same commit | ratchet (present, at most 20 lines), review (content) |
| AR08 | Re-export only in the feature's public entry; importers use the defining module. The public entry has no side effects (no route mounting, no engine import) | review |
| AR09 | Dependencies: feature uses `infra`; feature uses another feature only through its public entry; core features do not import other features; `infra` does not import features | linter |
| AR10 | Tests beside the code in `features/<f>/tests/test_<module>.<ext>`; harness with its own name (`<subject>_harness`); a test class imported by another file gets an alias starting with `_` | review |
| AR11 | Mocks and monkeypatches target the module of the caller, not the definer nor a re-export: a misplaced patch does not fail, it just stops having effect | review |
| AR12 | Moving code is done by script (line ranges or AST), never retyped; the model decides the map and fixes imports | review |
| AR13 | The TRD is 1:1 with the features: `docs/trd/<f>.md` is the technical map of the folder, and its `CLAUDE.md` points to it | review |
| AR14 | Paths computed from the module's own location use its real depth; after moving, check them | review |

## How to check
- `scripts/gates.sh ratchet` is the ratchet: it fails when a "ratchet" rule is violated outside the allowlist, and the allowlist only shrinks.
- `scripts/gates.sh lint` runs the linter rules for function and class size, inheritance and import direction (configured per stack in `ai-kit.json`); `scripts/gates.sh imports` catches import cycles.

## When creating something new
1. Find the feature by the PRD ID (`docs/prd/INDEX.md`) and read its `CLAUDE.md`.
2. Create the module named after its responsibility, with the IDs in its docstring.
3. Write the test in `features/<f>/tests/`, citing the ID.
4. Update the feature's `CLAUDE.md` and TRD in the same commit.
5. Run only the tests related to what you touched; the full suite runs once, at the end of the delivery.

# Stack recipes

The kit is stack-free; `/ai-kit install` adapts it to each project with these recipes. A recipe is data, not code: how to detect the ecosystem, which commands fill `ai-kit.json`, how the stack's linter enforces the structure rules that text cannot see (AR03 function and class size, AR04 inheritance, AR05 shared state, AR09 import direction), and what CI needs.

The installer reads only the recipes whose detection signals match, and **verifies every command by running it** before writing it. A recipe is a starting point; the project's own scripts and configuration win (an existing `make test`, `npm run test:unit`, `just lint` is used as is).

| Recipe | Detect |
|---|---|
| [python.md](python.md) | `pyproject.toml`, `setup.cfg`, `requirements*.txt`, `uv.lock`, `poetry.lock` |
| [node.md](node.md) | `package.json` (JavaScript or TypeScript, any framework) |
| [go.md](go.md) | `go.mod` |
| [jvm.md](jvm.md) | `build.gradle(.kts)`, `pom.xml` (Java, Kotlin) |
| [dotnet.md](dotnet.md) | `*.csproj`, `*.sln` |
| [rust.md](rust.md) | `Cargo.toml` |
| [ruby.md](ruby.md) | `Gemfile` |
| [php.md](php.md) | `composer.json` |
| [generic.md](generic.md) | Nothing above matches, or an ecosystem not listed |

In a monorepo, the root `commands` call the workspace runner (`pnpm -r`, `turbo run`, `nx run-many`, `go test ./...`, `make`, or one command per package joined with `&&`), so `scripts/gates.sh` stays the single entry point; `source_dirs` lists every package source folder.

## Recipe format
Every recipe has the same sections, so the installer reads them the same way:

1. **Detect**: files and what they reveal (package manager, framework, test runner).
2. **Commands**: the values for `ai-kit.json` `commands` and `tests`.
3. **Structure enforcement**: linter rules for AR03, AR04, AR05, AR09 with the kit's limits, and how to baseline existing violations so CI is green on day one.
4. **Offline guard**: how the unit tier is kept off the network and the database.
5. **CI setup**: the step that replaces the placeholder in `ci.yml`.
6. **Ignore**: generated paths for `ai-kit.json` `ignore` and `.gitleaks.toml`.

# Go

## Detect
| Signal | Means |
|---|---|
| `go.mod` | module path, Go version |
| `.golangci.yml` | golangci-lint configured |
| `//go:build integration` tags | integration tier selected by build tag |

## Commands
| Key | Value |
|---|---|
| `commands.test` | `go test` |
| `commands.offline_args` | `./...` (integration tests behind the `integration` build tag are excluded by default) |
| `commands.integration_args` | `-tags integration ./...` |
| `commands.no_coverage_args` | empty |
| `commands.lint` | `gofmt -l . \| (! grep .) && go vet ./... && golangci-lint run` |
| `commands.fix` | `gofmt -w . && golangci-lint run --fix` |
| `commands.import_check` | `go build ./...` (the compiler rejects cycles) |
| `tests.runner` | `go test {files}` with `{files}` as package paths (the related-test script lists files; the installer sets the runner to the packages of those files: `go test $(dirname of each)`) |
| `tests.native_related` | `go test $(go list -f '{{.Dir}}' {changed} 2>/dev/null \| sort -u)`, or leave empty and use the package of each changed file |
| `tests.failure_regex` | `^--- FAIL: (\S+)` |

## Structure enforcement
golangci-lint linters:
- `funlen` with `lines: 80` (AR03 functions; statements left at the default);
- module length: `scripts/ratchet.py` (500 lines per file);
- import direction (AR09): `depguard` rules per package, or `go-arch-lint`;
- AR04 does not apply (no inheritance); AR05: review package-level mutable variables.
Baseline: golangci-lint `issues.new-from-rev: <install commit>` reports only new violations; lower over time.

| Rule | Tool | Baseline |
|---|---|---|
| AR24 complexity | golangci-lint `gocyclo` (`min-complexity: 10`) or `cyclop` (`max-complexity: 10`), `nestif` (`min-complexity: 4`), `revive` `argument-limit` (5), `gocognit` optional | `new-from-rev` |
| AR25 dead code | `unused` (staticcheck U1000, in golangci-lint by default), `deadcode ./...` (golang.org/x/tools) for unreachable functions | `new-from-rev`, `//nolint:unused` with a reason |
| AR26 duplicates | golangci-lint `dupl` (`threshold: 100`), or `jscpd` | `new-from-rev` |
| AR27 typing | not applicable (statically typed) | |
| AR22 dispatch | `reflect` calls by computed name are review; `forbidigo` can forbid `reflect.Value.MethodByName` and `plugin.Open` | linter plus review |

## Offline guard
Unit tests use interfaces and fakes; network and database tests carry `//go:build integration`. Under the offline flag, a `TestMain` in packages with clients can fail when a real dial happens (custom `net.Dialer` in the client constructors).

## CI setup
```yaml
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - name: Download modules
        run: go mod download
```

## Ignore
`**/vendor/**`, `**/bin/**`.

## Layout
| Layout | Declare |
|---|---|
| `internal/<domain>/` packages (one per feature) | `layout: "One package per domain under internal/"`, `feature_root: "internal"` |
| `cmd/<binary>/` plus `internal/` plus `pkg/` | `layout: "Binaries in cmd/, domain packages in internal/, shared packages in pkg/"`, `map_dirs: ["cmd", "internal", "pkg"]`, areas from the packages under `internal` |
| By layer (`handlers/`, `service/`, `repository/`, `model/`) | `layout: "Packages by technical role (handlers, service, repository, model); product areas spread across them"`, `areas` per PRD area by file name, `map_dirs` the layer packages |
| Multi-module (`go.work`, several `go.mod`) | `layout: "Go workspace with one module per domain"`, one area per module: `areas: {"<m>": ["<m>/**"]}` |

A Go package is a folder: AR23 (20 files per folder) pushes large packages into sub-packages.

## Test naming
- `tests.mirror_patterns`: `["{name}_test"]`; `tests.match_symbol: true` (a package-level test names the symbols it proves, not the file).
- Tests sit beside the code in the same package folder (`foo_test.go`, Go requires it); integration tests behind a build tag, `testdata/` for fixtures (AR10).
- `tests.junit_xml`: `gotestsum --junitfile reports/junit.xml -- ./...` as the runner prefix, or `go test -json ./... | go-junit-report -parser gojson > reports/junit.xml` (look up the flag of the installed version).

## Generated files
`generated_patterns`: `**/*.pb.go`, `**/*_gen.go`, `**/*.gen.go`, `**/mock_*.go`, `**/*_string.go`, the ent output folders except `ent/schema` (hand-written schema files live there; never `**/ent/**`), sqlc output. Marker: Go's standard `// Code generated ... DO NOT EDIT.` (golangci-lint and gopls already honor it, and the ratchet's default marker regex matches it); a generator whose header matches none sets `generated_marker`.

## Framework exemptions
- `unique_name_exempt`: `main.go`, `doc.go`, `types.go`, `errors.go`, `handler.go`, `service.go`, `repository.go` (names repeated across packages by convention), `tools.go`.
- AR04 not applicable; embedding a struct is allowed. AR05: package-level `var` is state: allowed when immutable or behind `sync`, `atomic` or a constructor; `init()` functions are review.
- `id_header_lines`: files open with `package` and imports, so raise it (for example 25) or put the ID in the package doc comment above `package`.

## Snapshots
Agents never run the golden-file update mode: the `-update` test flag many projects define, `UPDATE_SNAPSHOTS=true` (cupaloy, go-snaps `UPDATE_SNAPS`); look up the project's own flag. Globs: `**/testdata/**/*.golden`, `**/*.golden`, `**/.snapshots/**`.

## Contracts
- gRPC or protobuf: the `.proto` files are the contract; `buf build -o -#format=json` or `buf breaking` (look up) for drift.
- OpenAPI from code: `swag init` (swaggo) or the project's generator writing `docs/swagger.json`; or the hand-written `openapi.yaml`.
- Database: sqlc `schema.sql` or `pg_dump --schema-only`.

## Setup
`commands.setup`: `go mod download` (plus `go generate ./...` when the repository generates code, and `go install` for tools pinned in `tools.go`).

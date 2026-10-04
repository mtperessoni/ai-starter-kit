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

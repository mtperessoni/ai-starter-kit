# .NET

## Detect
| Signal | Means |
|---|---|
| `*.sln`, `*.csproj` | projects; test projects reference `Microsoft.NET.Test.Sdk` |
| xUnit, NUnit or MSTest packages | test framework; `[Trait("Category","Integration")]` or `[Category]` separates tiers |
| `.editorconfig`, `Directory.Build.props` | analyzers and style already configured |

## Commands
| Key | Value |
|---|---|
| `commands.test` | `dotnet test` |
| `commands.offline_args` | `--filter "Category!=Integration"` |
| `commands.integration_args` | `--filter "Category=Integration"` |
| `commands.no_coverage_args` | empty |
| `commands.lint` | `dotnet format --verify-no-changes && dotnet build -warnaserror` |
| `commands.fix` | `dotnet format` |
| `commands.import_check` | `dotnet build` |
| `tests.runner` | `dotnet test --filter "{filter}"`, the installer turning each file into `FullyQualifiedName~<ClassName>` joined with `\|` |
| `tests.native_related` | empty |
| `tests.failure_regex` | `^\s*Failed (\S+)` |

## Structure enforcement
- Method length (AR03): SonarAnalyzer.CSharp rule `S138` (functions should not have too many lines) set to 80; file length by `scripts/ratchet.py`.
- Import direction and inheritance (AR04, AR09): NetArchTest or ArchUnitNET tests in the test tier.
- Baseline: rule severities as warnings plus a shrink-only suppression file; promote to errors per wave.

## Offline guard
Unit tests use fakes; integration tests carry the Integration category. Under the offline flag, an `HttpMessageHandler` that throws can be registered in the test host.

## CI setup
```yaml
      - uses: actions/setup-dotnet@v4
        with:
          global-json-file: global.json
      - name: Restore
        run: dotnet restore --locked-mode
```

## Ignore
`**/bin/**`, `**/obj/**`.

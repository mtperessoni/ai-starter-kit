# Testing · TRD

How to test in this repository. Rules the tests protect: [invariants.md](invariants.md). Constitution, test-first principle: the unit suite runs offline, with no network and no keys.

## Targets of `scripts/gates.sh`

| Target | Runs | Use when |
|---|---|---|
| `related [files]` | The ratchet, then the mirror test and the importers of the changed files | While working, after every change |
| `one <file>` | One test file, offline | Writing a test |
| `offline` | The whole suite | Once, at the end of a delivery |
| `baseline <slug>` | `offline`, then records its failures | Before the first code task of a delivery |
| `compare <slug>` | `offline`, then prints only failures not in the baseline | At the end of a delivery |

The stack commands behind each target are `python -m pytest` with the options in `ai-kit.json`.

While working, run only the related tests; the full suite runs once, at the end of a delivery, compared with the baseline.

## Where tests live

Feature tests beside the code in `src/storefront/features/<f>/tests/` (AR10). Root `tests/` holds what is not one feature's.

## Configuration

| Item | Value |
|---|---|
| Markers | none |
| Default options | quiet output |
| Test paths | `src`, `tests` (`pyproject.toml`, `pythonpath = ["src"]`) |

## Fakes

None: the code has no external service.

## Patterns that avoid rework

- Feature tests cite the PRD ID they prove (AR06).
- A test goes through the public function of the feature, not through its private helpers.

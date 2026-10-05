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

Feature tests beside the code in `src/market/features/<f>/tests/test_<module>.py`, one per module (AR10). Infra tests in `src/market/infra/tests/`. API smoke tests in `src/market/tests/test_api.py`. `conftest.py` at the project root has an autouse fixture calling `market.infra.repositories.reset_all()`.

## Configuration

| Item | Value |
|---|---|
| Markers | none |
| Default options | quiet output |
| Test paths | `src` (`pyproject.toml`, `pythonpath = ["src"]`, `testpaths = ["src"]`) |

## Fakes

None: the code has no external service. The payment gateway is a deterministic fake chosen by token (`ok_*`, `decline_*`, `fraud_*`, `flaky_N`, `timeout_always`). Time moves with `set_now` and `advance`.

## Patterns that avoid rework

- Feature tests cite the PRD ID they prove (AR06).
- A test goes through the public function of the feature, not through its private helpers; the engine is tested per stage and in allowed pairs.
- Declines in checkout tests use no limited coupon unless the test is about that.

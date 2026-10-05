# Testing · TRD

How to test in this repository. Rules the tests protect: [invariants.md](invariants.md). Constitution, test-first principle: the unit suite runs offline, with no network and no keys.

## Targets of `scripts/gates.sh`

| Target | Runs | Use when |
|---|---|---|
| `related [files]` | The ratchet, then the mirror test and the importers of the changed files (`scripts/related_tests.py --run`) | While working, after every change |
| `one <file>` | One test file, offline, no coverage threshold | Writing a test |
| `offline` | The whole unit tier with no network and no database; the script sets that environment itself | Once, at the end of a delivery |
| `baseline <slug>` | `offline`, then records its failures in `.claude/prd-gate/state/<slug>/baseline-failures.txt` | Before the first code task of a delivery |
| `compare <slug>` | `offline`, then prints only failures not in the baseline | At the end of a delivery |
| `integration` | The integration tier (needs a database): guards first, cleanup on every exit | When there is a database |
| `full` | Everything, with the same guards and cleanup | Before merge, on a machine with a database |
| `build [args]` | `docker compose build` with the same guards and cleanup | The only way to build images |
| `guard` | Free disk, labelled image cap, cap over all images, Docker disk file warning | Before anything that builds or pulls |
| `sweep` | Removes test-labelled containers, volumes and networks older than `DOCKER_STALE_MINUTES` | After a killed run; the integration session also runs it |
| `docker-clean` | Every labelled leftover of any age, bounded build cache; lists other projects' images | When no test of this repository is running |
| `clean-outputs` | Deletes background task outputs older than 2 days or over 200 MB | Any time; Docker targets run it on exit |
| `lint` | Lint, format check, type check: verifies | Before returning or committing |
| `fix` | Repairs lint and format | Then run `lint` |

CI (`.github/workflows/ci.yml`): lint, ratchet, `offline`, `full`, secret scan.

While working, run only the related tests; the full suite runs once, at the end of a delivery, compared with the baseline.

## Containers

Without a `docker` section in `ai-kit.json`, the Docker targets do nothing.

| Item | Value |
|---|---|
| Labels | `<namespace>.repo=<repo>`, `<namespace>.purpose=test\|dev\|spike` (`ai-kit.json` "docker") |
| Tests that build images | `<the tests that prove services start together; built once per session>` |
| Session sweep | `<the integration tier's session setup that runs the sweep at start and end>` |
| Limits (env) | `MIN_FREE_GB` 10, `IMAGE_CAP` 8, `IMAGE_CAP_GB` 6, `TOTAL_IMAGE_CAP_GB` 20, `BUILD_CACHE_MAX_GB` 3, `DOCKER_STALE_MINUTES` 60, `DOCKER_DISK_WARN_GB` 40 |

## Where tests live

Feature tests beside the code in `<src>/features/<f>/tests/` (AR10). Harnesses have their own name (`<subject>_harness`). Root `tests/` holds what is not one feature's: structural tests, integration, evaluation against real services, shared fakes.

## Configuration

| Item | Value |
|---|---|
| Markers | `<eval: needs a real model or the network, never in CI gates>` |
| Default options | `<for example: exclude eval, coverage on src, per-test timeout>` |
| Test paths | `<tests, src/features>` |

## Guards

| Where | What it does |
|---|---|
| `<root test setup>` | Blocks outbound network outside loopback; under the offline flag also blocks loopback and database connections, failing instead of skipping |

## Fakes

| File | Fakes |
|---|---|
| `<tests/fakes/...>` | `<what it replaces>` |

## Patterns that avoid rework

- Mocks and patches target the module of the caller, not the definer nor a re-export (AR11).
- Feature tests cite the PRD ID they prove (AR06).
- A test that needs a real service goes behind the `eval` marker.

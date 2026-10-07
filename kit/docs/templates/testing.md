# Testing · TRD

How to test in this repository. Rules the tests protect: [invariants.md](invariants.md). Constitution, test-first principle: the unit suite runs offline, with no network and no keys.

## Targets of `scripts/gates.sh`

| Target | Runs | Use when |
|---|---|---|
| `related [files]` | The ratchet, then the mirror test and the importers of the changed files (`scripts/related_tests.py --run`); prints its wall time and warns above `tests.related_budget_seconds` (TS37), warns when snapshots changed | While working, after every change |
| `one <file>` | One test file, offline, no coverage threshold | Writing a test |
| `offline` | The whole unit tier with no network and no database; the script sets that environment itself | Once, at the end of a delivery |
| `baseline <slug>` | `offline`, then records its failures in `.claude/prd-flow/state/<slug>/baseline-failures.txt` | Before the first code task of a delivery |
| `compare <slug>` | `offline`, then prints only failures not in the baseline | At the end of a delivery |
| `integration` | The integration tier (needs a database): guards first, cleanup on every exit | When there is a database |
| `full` | Everything, with the same guards and cleanup | Before merge, on a machine with a database |
| `build [args]` | `docker compose build` with the same guards and cleanup | The only way to build images |
| `guard` | Free disk, labelled image cap, cap over all images, Docker disk file warning | Before anything that builds or pulls |
| `sweep` | Removes test-labelled containers, volumes and networks older than `DOCKER_STALE_MINUTES` | After a killed run; the integration session also runs it |
| `docker-clean` | Every labelled leftover of any age, bounded build cache; lists other projects' images | When no test of this repository is running |
| `clean-outputs` | Deletes background task outputs older than 2 days or over 200 MB | Any time; Docker targets run it on exit |
| `setup` | `commands.setup`: makes a fresh clone or worktree ready to test | First thing in a new clone or worktree |
| `hotspots` | Files ranked by recent commits times lines, marking those over the limits | Ordering legacy work |
| `contracts` | Fails when a schema or contract snapshot drifted from its source | After changing a schema or contract |
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

Per AR10: beside the code in `<area folder>/tests/` when the stack allows, otherwise the stack's mirrored tree with the same relative path. A test file is named after its module with one of `tests.mirror_patterns` (`ai-kit.json`), so `related` finds it. Harnesses have their own name (`<subject>_harness`). Root `tests/` holds what is not one area's: structural tests, integration, evaluation against real services, shared fakes.

This repository: `<beside the code or mirrored tree, and the patterns in use>`.

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

## Reliability

| Topic | Rule |
|---|---|
| Flaky (TS38) | A test that failed and passed on the same code goes to `tests.flaky` with date and cause; `new_failures.py` reports it as flaky, not new; the list shrinks |
| Snapshots (TS39) | Never updated to make a test pass; update mode only for a change whose PRD ID changed the expected output, named in the return |
| Parallel-safe (TS40) | No fixed ports, shared files or shared database names; own temp dir and unique resource names per test |
| Builders (TS41) | Test data from small builders or factories per subject beside the tests; no shared fixture file past the module limit |
| Characterization (TS42) | Before changing legacy code without tests, a golden master or approval test records today's behavior, citing the area |

## Contract snapshots

| Snapshot | Source | Command | Consumer |
|---|---|---|---|
| `<file>` | `<schema or contract it freezes>` | `scripts/gates.sh contracts` | `<sibling repository that consumes it, from repo.md>` |

Proposed when `repo.md` lists a sibling consumer and none is configured (K-74). Delete the table when the repository has no consumer.

## Patterns that avoid rework

- Mocks and patches target the module of the caller, not the definer nor a re-export (AR11).
- Tests cite the PRD ID they prove (AR06).
- A test that needs a real service goes behind the `eval` marker.

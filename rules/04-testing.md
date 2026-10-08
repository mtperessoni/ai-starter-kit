# Testing (TS)

Tests run narrow while working and wide once. Before these rules, agents took 13 to 14 minutes per task because each ran the whole unit suite (4 to 5 minutes per run) and parallel agents broke each other's test collection.

## While working

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS01 | Test first: write the task's test, run it and see it fail, implement the minimum, run it again | A test that never failed proves nothing | workers/executor.md step 2; constitution |
| TS02 | During work run only the **related tests**: the mirror test of the module, every test that imports or uses the touched module (`Grep` the module path in the test folders), the architecture ratchet, plus lint and format of the touched files | Related tests catch the regressions that matter at a fraction of the time | workers/executor.md step 3; execution.md E18; AGENTS.md |
| TS03 | **The full suite runs once**, at the end of a delivery, in the main thread, after all tasks are applied. Then a closing task fixes the tests and the code that are wrong according to the PRD | One full run instead of one per task and per review round | execution.md E18; review.md V09 |
| TS04 | **Baseline:** before code, the failures of the last recorded full run go to `state/<slug>/baseline-failures.txt` (if none is recorded, run the full suite once first). At the end only new failures count | Pre-existing failures otherwise get blamed on, or fixed by, the wrong task | execution.md E03 |
| TS05 | A failing test unrelated to what you touched is not investigated in the middle of a task; it waits for the end | Mid-task investigations derail the wave | execution.md E18 |
| TS06 | Single-file runs disable the coverage threshold (`--no-cov` or equivalent); the threshold applies to the full run only | A single file never meets a repo-wide threshold | testing.md |
| TS07 | `scripts/related_tests.py` turns the changed files into the list of related tests (mirror test plus importers) and runs them with the stack's runner from `ai-kit.json`; when the stack has a native related-test runner, `ai-kit.json` points to it instead | One command, any stack | `scripts/related_tests.py`; `scripts/gates.sh related` |
| TS08 | Test output goes to a file; only failures and the summary come back into context | Logs are thousands of lines | SA25 |
| TS09 | A test of another file that broke as a direct, expected consequence of the change may have only its expectation adjusted, never a loosened safety assertion, and goes into the return's file list. A contract or rule divergence stops the task and returns as a gap | Silent assertion loosening is how regressions ship | workers/executor.md step 5 |
| TS10 | In a refactor with huge test files: first split the code and the big test files, and only then run tests, in parts. During the split the proof is static: import of the package (catches cycles), type check and lint | Running tests on half-moved code produces noise, not signal | execution.md E19; LS |

## Suite design

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS11 | The unit suite runs offline and deterministic: fake models and fake external services by default. A test that needs the network or a real model goes behind a marker (`eval`) and never gates a merge | A gate that depends on the network is flaky and expensive | constitution (test-first principle); AGENTS.md |
| TS12 | **The safe path is the invoked one.** The gate script sets its own environment (unsets database URLs, sets an offline flag) instead of relying on the caller's shell. Touching the network or a database under the offline flag fails, it does not skip | A leaked variable once made the "offline" number be the full run's number, and two equal numbers looked like confirmation | `scripts/gates.*`; testing.md |
| TS13 | Do not compare test totals to prove two gates differ; ask each gate what it collects (a `divergence` target) | A leaked variable changes what runs and skips, never what is collected | testing.md |
| TS14 | The integration tier is not collected by the offline target at all (ignored path), not merely refused at connect time | Session-scoped fixtures start containers before function-scoped guards exist | testing.md |
| TS15 | Every test cites the PRD rule ID it proves (docstring or test name) | `Grep "<ID>"` finds rule, code and test together | AR06; DS |
| TS16 | Tests live as AR10 says; harnesses have their own name (`<subject>_harness`), never a generic one | Locality; generic names collide | AR10 |
| TS17 | Mocks and monkeypatches target the module of the **caller**, not the module that defines the name nor a re-export | A patch in the wrong place does not fail, it just stops having effect | AR11 |
| TS18 | Root-level test configuration (for example `conftest.py` with autouse guards) lives at the repository root, so tests inside feature folders get the same guards | Moving tests beside code once ran 119 tests without the offline guard | LS |
| TS19 | Lint has two targets: one that verifies (as CI does) and one that repairs; agents run the verifying one before returning | Agents that only "fix" hide what they changed | testing.md |
| TS20 | CI runs the offline gate before the full one and asserts the two disagree | Proves isolation on every merge | `.github/workflows/ci.yml` |
| TS21 | The gate is tested by executing it: a test runs the offline gate against a canary that touches a database and asserts it exits non-zero **because of the guard** (not because of coverage, collection or a missing file). Never test a gate by checking that words are present in its script | With the test command replaced by `true`, every "the script contains X" pin stayed green | `tests/` gate tests; testing.md |
| TS22 | `scripts/new_failures.py` compares a test log with `baseline-failures.txt` and prints only new failures | Makes TS04 one command in any stack | `scripts/gates.sh compare` |

## Speed and reliability

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS37 | Feedback budget: `scripts/gates.sh related` prints its wall time and warns above `tests.related_budget_seconds`; with `tests.junit_xml` set it lists the slowest tests. Over budget is a readiness finding (split the slow test or its fixture), never a reason to skip related tests | The related run is paid on every task; without a measured budget it creeps up unnoticed until agents skip it | `scripts/related_tests.py` |
| TS38 | A test that failed and passed on the same code goes to `tests.flaky` with its date and the cause when known; `new_failures.py` reports it as flaky, not new; the list shrinks as each one is fixed or deleted | A flaky failure read as new sends the agent hunting a regression it did not cause, and read as noise it hides a real one | `scripts/new_failures.py`; review |
| TS39 | Snapshot and golden files (`tests.snapshot_patterns`) are never updated to make a test pass: the runner's update mode runs only for a change whose PRD ID changed the expected output, named in the return; `related` flags a change that touches them | Regenerating a snapshot turns a failing test green without proving anything, the same loosening as TS09 | `scripts/related_tests.py`; review |
| TS40 | Tests are parallel-safe: no fixed ports, shared files or shared database names; each test gets its own temp dir and unique resource names, so parallel agents and worktrees never break each other | Two agents running tests at once collide on the same port or file and both see failures neither caused | review; testing.md |
| TS41 | Test data comes from small builders or factories per subject beside the tests; test-support files obey the module limit; no shared fixture file grows past it | One shared fixture file grows with every test, is read whole by every agent and breaks unrelated tests when it changes | ratchet (module limit); review |
| TS42 | Before changing legacy code without tests, a characterization test (golden master or approval test) records today's behavior of the touched path, citing the area; then the change | Without a recorded behavior the agent cannot tell a fix from a regression in code nobody specified | review; readiness plan |

## Containers and disk

Measured on one Windows machine in a single day of agent work: about 44 GB of unbounded background task output, and a Docker disk file of 49.5 GB with 19 GB in use. A first fix (labels, caps, a manual cleanup) still leaked, because it relied on a test `finally` and on someone running the cleanup.

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS27 | Build an image only for a test that proves services start together; everything else uses a throwaway database container (testcontainers or equivalent) or in-process fakes. Images are built once per test session, never per module | Building images is the most expensive thing a test does, in time and in disk | testing.md "Containers"; AGENTS.md |
| TS28 | Every image, container, volume and network the repository creates carries `<namespace>.repo=<repo>` and `<namespace>.purpose=test\|dev\|spike` (named in `ai-kit.json` "docker"), one tag per image. Stacks started by tests are `purpose=test`; the dev stack is `dev` | Only labelled objects can be cleaned without touching another project; `test` versus `dev` lets a sweep run next to a developer's stack | `ai-kit.json`; compose files; stack recipe |
| TS29 | Build and pull only through `scripts/gates.sh build\|integration\|full`: they refuse below `MIN_FREE_GB` free, above the labelled image cap (`IMAGE_CAP`, `IMAGE_CAP_GB`) or the cap over all images (`TOTAL_IMAGE_CAP_GB`) | A full disk stopped agents mid-write and corrupted a container snapshot | `scripts/docker_hygiene.py`; `scripts/gates.sh` |
| TS30 | Those targets clean up from an `EXIT` trap, so a failed or interrupted run cleans up too: sweep, build cache bounded by size (`--max-used-space`, `BUILD_CACHE_MAX_GB`), old task outputs deleted. Never bound the cache with an age filter | `--filter until=24h` keeps everything built today; `--keep-storage` became a floor, not a ceiling | `scripts/gates.sh`; TS21 test with a fake Docker |
| TS31 | A killed run cannot clean up after itself. The integration tier's session setup sweeps test-labelled containers, volumes and networks older than `DOCKER_STALE_MINUTES` at start and at end; younger ones may be another session's live run and stay | Agents run the test runner directly, past the gates, and get killed by tool timeouts mid-stack | stack recipe; `scripts/gates.sh sweep` |
| TS32 | A teardown that fails (`compose down`, container stop) fails the test session; it is never ignored | An ignored `down` failure leaves the stack and nobody learns of it | stack recipe |
| TS33 | A one-off container is `--rm` and labelled `purpose=test`; an image pulled only for it is removed in the same step. A spike removes its images, and the third-party images it pulled, when it ends | Helper and spike images are the ones nobody remembers | AGENTS.md |
| TS34 | Background commands have bounded output: no `tail -f`, no printing poll loops; output goes to a file under `clean-outputs`' care | One unbounded background output filled tens of GB | AGENTS.md; `scripts/clean_task_outputs.py` |
| TS35 | On Docker Desktop, space freed inside Docker returns to the host only when Docker Desktop is quit, or after compacting the disk file as admin. The guard warns above `DOCKER_DISK_WARN_GB` with the steps | The disk file never shrinks by itself: 49.5 GB on disk for 19 GB in use | `scripts/docker_hygiene.py check-docker-disk` |
| TS36 | A script that shells out to bash on Windows finds Git Bash, never `C:\Windows\System32\bash.exe` (the WSL launcher) | With the WSL launcher first on `PATH`, the guards silently never ran | `tests/` gate tests; stack recipe |

## CI

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS23 | CI runs on pull requests and on pushes to every branch that deploys | A gate that runs only before a merge checks the parts and never the sum; measured: a deploy branch had seven deploys and zero CI runs | `.github/workflows/ci.yml` |
| TS24 | A pull request cancels its own earlier runs; a push to a deploy branch never does | Cancelling the check while the deploy proceeds ships an artifact whose check never concluded; measured: three images deployed, zero completed CI runs | `.github/workflows/ci.yml` |
| TS25 | Every CI job has a timeout (about 15 minutes) | A run stuck past it is hung, not slow | `.github/workflows/ci.yml` |
| TS26 | CI order: lint, ratchet, docs gate, offline gate, full suite; secret scan as a separate job | Cheap checks fail first | `.github/workflows/ci.yml` |

# Testing (TS)

Tests run narrow while working and wide once. Before these rules, agents took 13 to 14 minutes per task because each ran the whole unit suite (4 to 5 minutes per run) and parallel agents broke each other's test collection.

## While working

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS01 | Test first: write the task's test, run it and see it fail, implement the minimum, run it again | A test that never failed proves nothing | workers.md "executor" step 2; constitution |
| TS02 | During work run only the **related tests**: the mirror test of the module, every test that imports or uses the touched module (`Grep` the module path in the test folders), the architecture ratchet, plus lint and format of the touched files | Related tests catch the regressions that matter at a fraction of the time | workers.md "executor" step 3; execution.md E18; AGENTS.md |
| TS03 | **The full suite runs once**, at the end of a delivery, in the main thread, after all tasks are applied. Then a closing task fixes the tests and the code that are wrong according to the PRD | One full run instead of one per task and per review round | execution.md E18; review.md V09 |
| TS04 | **Baseline:** before code, the failures of the last recorded full run go to `state/<slug>/baseline-failures.txt` (if none is recorded, run the full suite once first). At the end only new failures count | Pre-existing failures otherwise get blamed on, or fixed by, the wrong task | execution.md E03 |
| TS05 | A failing test unrelated to what you touched is not investigated in the middle of a task; it waits for the end | Mid-task investigations derail the wave | execution.md E18 |
| TS06 | Single-file runs disable the coverage threshold (`--no-cov` or equivalent); the threshold applies to the full run only | A single file never meets a repo-wide threshold | testing.md |
| TS07 | `scripts/related_tests.py` turns the changed files into the list of related tests (mirror test plus importers) and runs them with the stack's runner from `ai-kit.json`; when the stack has a native related-test runner, `ai-kit.json` points to it instead | One command, any stack | `scripts/related_tests.py`; `scripts/gates.sh related` |
| TS08 | Test output goes to a file; only failures and the summary come back into context | Logs are thousands of lines | SA25 |
| TS09 | A test of another file that broke as a direct, expected consequence of the change may have only its expectation adjusted, never a loosened safety assertion, and goes into the return's file list. A contract or rule divergence stops the task and returns as a gap | Silent assertion loosening is how regressions ship | workers.md "executor" step 5 |
| TS10 | In a refactor with huge test files: first split the code and the big test files, and only then run tests, in parts. During the split the proof is static: import of the package (catches cycles), type check and lint | Running tests on half-moved code produces noise, not signal | execution.md E19; LS |

## Suite design

| ID | Rule | Why | Lands in |
|---|---|---|---|
| TS11 | The unit suite runs offline and deterministic: fake models and fake external services by default. A test that needs the network or a real model goes behind a marker (`eval`) and never gates a merge | A gate that depends on the network is flaky and expensive | constitution (test-first principle); AGENTS.md |
| TS12 | **The safe path is the invoked one.** The gate script sets its own environment (unsets database URLs, sets an offline flag) instead of relying on the caller's shell. Touching the network or a database under the offline flag fails, it does not skip | A leaked variable once made the "offline" number be the full run's number, and two equal numbers looked like confirmation | `scripts/gates.*`; testing.md |
| TS13 | Do not compare test totals to prove two gates differ; ask each gate what it collects (a `divergence` target) | A leaked variable changes what runs and skips, never what is collected | testing.md |
| TS14 | The integration tier is not collected by the offline target at all (ignored path), not merely refused at connect time | Session-scoped fixtures start containers before function-scoped guards exist | testing.md |
| TS15 | Every test cites the PRD rule ID it proves (docstring or test name) | `Grep "<ID>"` finds rule, code and test together | AR06; DS |
| TS16 | Tests live beside the code in `features/<f>/tests/`; test harnesses have their own name (`<subject>_harness`), never a generic one | Locality; generic names collide | AR10 |
| TS17 | Mocks and monkeypatches target the module of the **caller**, not the module that defines the name nor a re-export | A patch in the wrong place does not fail, it just stops having effect | AR11 |
| TS18 | Root-level test configuration (for example `conftest.py` with autouse guards) lives at the repository root, so tests inside feature folders get the same guards | Moving tests beside code once ran 119 tests without the offline guard | LS |
| TS19 | Lint has two targets: one that verifies (as CI does) and one that repairs; agents run the verifying one before returning | Agents that only "fix" hide what they changed | testing.md |
| TS20 | CI runs the offline gate before the full one and asserts the two disagree | Proves isolation on every merge | `.github/workflows/ci.yml` |
| TS21 | The gate is tested by executing it: a test runs the offline gate against a canary that touches a database and asserts it exits non-zero **because of the guard** (not because of coverage, collection or a missing file). Never test a gate by checking that words are present in its script | With the test command replaced by `true`, every "the script contains X" pin stayed green | `tests/` gate tests; testing.md |
| TS22 | `scripts/new_failures.py` compares a test log with `baseline-failures.txt` and prints only new failures | Makes TS04 one command in any stack | `scripts/gates.sh compare` |

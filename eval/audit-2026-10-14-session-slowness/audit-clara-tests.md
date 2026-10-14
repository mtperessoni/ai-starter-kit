# clara-ai test audit (read-only, 2026-10-14, branch feat/sara-speech-boundary)

## 1. Startup and collection
| Item | Measured |
|---|---|
| test files | 540 (266 under tests/, 274 under src/features/*/tests); not ~266 |
| collect-only (`.venv`, --no-cov) | 7682 of 7866 collected (184 eval deselected) in 10.4 s, wall 14.6 s |
| one small file (tests/unit/domain/test_config_registry.py) | 10 tests, 0.09 s, 1.3 s wall |
| import of the transport app (`-X importtime features.text.socket.transport`) | 1.1 s (fastapi 0.26 s, turn_service 0.44 s), paid once per process |
| pytest addopts (pyproject.toml:215) | `-m "not eval" --cov=src --cov-report=term-missing --timeout=90`: coverage ON by default on every targeted run |
| plugins | anyio, langsmith, asyncio (auto), cov, timeout; no xdist (suite is serial) |
| autouse fixtures (conftest.py) | agent keys off, outbound network block, unit-context default; cheap |
Verdict: collection is not the problem. Coverage on by default adds overhead to each targeted run (not measured separately).

## 2. Slowness and hang candidates (main finding)
pytest-timeout IS configured: 90 s per test (thread method), 0 per-test `mark.timeout`. So a 600 s command is not one hung test; it is many slow tests or a long run under the 600 s tool cap.
| Evidence | Detail |
|---|---|
| tests/unit/api/text/test_encounter_ending.py | 27 tests, 94.8 s (3.5 s per test); single test 4.75 s. cProfile: 2.7 s of 5.1 s idle in `GetQueuedCompletionStatus` (event loop waiting), start_blocking_portal from Starlette TestClient websockets |
| tests/unit/api/text/test_close_reasons_and_deployment.py | 34 tests, 38.9 s (3.5-3.8 s per websocket test) |
| tests/unit/api/acceptance | 112 tests, 12 s, 2 FAIL (test_the_context_sections_in_both_engines.py test_14_with_the_key_off_the_block_still_leaves..., [texto]); unit baseline is not green |
| full unit + src/features run | `pytest tests/unit src/features --no-cov` was at ~7% after 280 s (killed by my cap); an earlier run reached 19% at 200 s. Extrapolated full run is well over 600 s, matching the "exactly 600 s" commands |
| datadog dogstatsd | stderr noise "offline-only run: connection to 127.0.0.1:8125 is blocked" during unit runs |
Top suspects (cost, not deadlock):
1. Websocket TestClient tests in tests/unit/api/text/* and speech_relay files: ~3.5 s each from real thread/loop waits; hundreds of them dominate the suite.
2. Real sleeps: tests/fakes/fake_alarm_classifier.py:60 (LateAlarmClassifier, default 0.3 s); asyncio.sleep(0.05-0.1) in tests/unit/api/test_context_orchestration_acceptance.py:347,370,395, test_speech_relay_assessment_only.py:185-315, test_sessions_conductor.py:107; time.sleep(0.05) polling in tests/integration/test_full_coverage.py:322,388 and test_patient_history_run.py:456. 37 files contain sleep.
3. Integration tier: tests/integration/conftest.py:34 starts a PostgresContainer (Docker); `migrated_url` is function-scoped and runs `subprocess.run(["alembic","upgrade","head"])` per test (conftest.py:53) plus DROP SCHEMA teardown (210 integration tests, 215 uses of migrated_url/admin_engine). test_migrations.py and test_stage_panel_persistence.py run alembic subprocesses with no timeout argument. Skips cleanly without Docker, so green-but-unverified is possible.
4. Subprocess: tests/unit/test_a_full_run_must_account_for_the_integration_tier.py:27, test_prd_flow_gate_script.py:57.
No real network or server start found in unit (socket guard blocks it; test_offline_guard.py uses loopback only).

## 3. Text-oracle tests
| Kind | Count | Notes |
|---|---|---|
| `assert "<literal 25+ chars>" in x` | 245 | mostly on built prompts/contexts/records, not on files |
| asserts with prompt/instructions on one side | ~130 outside tests/eval; ~65 `in prompt` forms | mostly check that code assembled patient data into the prompt |
| tests reading markdown/PRD/prompt files and asserting phrases | ~2 (test_prd_flow_gate_script.py runs the gate on a tmp repo; test_architecture.py checks PRD id citation) | rare pattern |
| structural guard tests | test_architecture.py, test_no_client_branching.py, test_the_exam_suggestion_is_internal.py (AST/path scans) | controls, not phrase pins |
| parity vs n8n | 9 tests (tests/parity/test_prompt_parity.py) | intentional, excluded |
Examples of pinned wording: tests/integration/test_patient_history_run.py:215 `"(mais recente: 128/82 em 2026-09-28 09:00)" in summary_user`; :273 `"Histórico do paciente: Hipertensa desde marco." in ...`; tests/eval/agent_quality/production_context/test_assessment_context_offline.py:197 `"Nao utilizar o questionario de alcool" in context.unit_context`. These pin formatter output but exercise real code with a fake model.

## 4. Lockstep with code (since 2026-10-01, HEAD history)
| Metric | Value |
|---|---|
| commits | 820 (496 non-merge touching src) |
| src + tests together | 454 (55%) |
| src only | 41 (5%) |
| tests only | 71 (9%) |
| neither (docs/chore) | 254 |
| assertions added vs removed (includes moves from the AR refactor) | +12,235 / -4,852 |
| test defs added vs removed | +3,927 / -1,618 (a large part is relocation to features/*/tests) |
| deleted test files | 29 |
| skip/xfail in tree | 27 skip sites: 24 eval key-missing, 1 Docker (integration), 1 parity contract unresolved, 1 skipif; 0 xfail; 21 added lines since Oct 1 (eval harnesses) |
Sample of fix commits: 4fc03394 (new 85-line test, 0 asserts removed, 3 added), 738b2f84 (new 59-line test, 4 asserts added, 0 removed), 0d1a7d27 (+4 test lines), 1827a4cf (+5), e06bc7fd (26+1 test, and the FAKE repository edited 16/9 to mirror new DB refusal). Pattern is additive: a new failing-case test ships with the fix; existing assertions are mostly not rewritten. Counter-signal: fakes are edited in lockstep with real behavior, which is where drift hides. Not measured: loosened assertions (needs per-diff review).

## 5. Fakes vs real behavior
13,542 assert lines in unit + features. About 448 (3%) assert on a fake/mock's recorded calls/prompts (`.calls .sent .prompts .captured call_count assert_called`); `assert_called*` only 24. MagicMock/monkeypatch/mock.patch: 390 occurrences in 121 files. 19 hand-written fakes in tests/fakes. Tautology (asserted value comes from a fake configured in the same test) cannot be proven by grep; a rough upper bound is about 3% plus scripted-reply tests. The suite is mostly real code over fakes at boundaries (DB, model, voice). Risk is fake fidelity, not tautology.

## 6. gate.py (.claude/skills/prd-flow/scripts/gate.py, 296 lines + 17 modules; pure python, no pytest)
| Run | Wall time | Result |
|---|---|---|
| default | 28.0 s | 2 ERROR G7 (REL-07, URG-12 reworded without CHANGELOG line), 4 warnings |
| --trace | 1.7 s | 10 errors G12 (rules without citing test, e.g. R4-04), 243 warnings |
| --final | 0.23 s | 126 errors G19 (rules still planned/pending), 71 warnings |
Checks: PRD markdown structure, rule rows vs CHANGELOG (G7), INDEX, TRD paths and symbols (G23-G26), plan cards and wave overlap (P*), decision sheets (S*), rule-to-test trace (G12), final state (G19-G21), sibling PRDs (G28), HTML freshness. 440 runs x 28 s default is at most ~3.4 h if all were default runs (upper bound; other modes are sub-2 s). The default run is the expensive mode and is currently red.

## Bottom line
- "Viciados" evidence is weak: tests are added with fixes, few call-record tautologies, almost no phrase-in-PRD oracle tests, guard tests are structural.
- Real cost drivers: (a) ~3.5 s per websocket TestClient test in tests/unit/api/text and speech_relay files; (b) full unit run exceeds 600 s serial, no xdist; (c) coverage on by default; (d) gate.py default 28 s and red; (e) integration alembic subprocess per test plus Docker; (f) unit baseline has red tests.
- Gaps: full suite wall time not completed (300 s cap); loosened assertions not measured; per-test tautology not provable by grep; staging branch not diffed separately.

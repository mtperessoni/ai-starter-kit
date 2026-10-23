# Python

## Detect
| Signal | Means |
|---|---|
| `uv.lock` | uv: prefix commands with `uv run`; install `uv sync --frozen` |
| `poetry.lock` | Poetry: `poetry run`; install `poetry install --no-interaction` |
| `requirements*.txt` only | pip in a virtualenv; install `pip install -r requirements.txt` |
| `[tool.pytest.ini_options]` or `pytest.ini` | pytest; read `addopts`, `testpaths`, `markers` |
| `pytest-cov` in dependencies | coverage flags exist: `--no-cov` disables the threshold |
| `[tool.ruff]`, `[tool.mypy]`, `pyrightconfig.json` | lint and type tools already chosen |

## Commands
| Key | Value |
|---|---|
| `commands.test` | `uv run pytest` |
| `commands.offline_args` | `--ignore=tests/integration` (the integration tier is not collected at all) |
| `commands.integration_args` | `tests/integration` |
| `commands.no_coverage_args` | `--no-cov` (only with pytest-cov) |
| `commands.lint` | `uv run ruff check . && uv run ruff format --check . && uv run mypy src` |
| `commands.fix` | `uv run ruff check --fix . && uv run ruff format .` |
| `commands.import_check` | `uv run python -c "import <entry module>"` with `PYTHONPATH` set as the app runs |
| `tests.runner` | `uv run pytest {files} --no-cov -q --junitxml=reports/junit.xml` (pytest keeps its cache provider on: `-p no:cacheprovider` is not used) |
| `tests.junit_xml` | `reports/junit.xml` (default on) |
| `tests.native_related` | empty (use `scripts/related_tests.py`) |
| `tests.failure_regex` | `^(?:FAILED\|ERROR)\s+(\S+)` (pytest's short summary) |
| `tests.no_tests_exit_codes` | `[5]` (pytest exits 5 when a chunk of `related` collects nothing; without it that chunk turns a green run red) |
| `tests.parallel_runner` | `uv run pytest {files} --no-cov -q -n auto --junitxml=reports/junit.xml` (pytest-xdist; used from `tests.parallel_from` selected files on and over the cap, so a big change never falls back to a whole folder in one process) |
| `tests.parallel_from` | `40` (below it one process is faster: starting the workers, each importing the app, costs more than the tests) |
| `tests.runner_args_file` | `true` with pytest 8.2 or later: the selection goes to one call as `@file`, one startup instead of one per command-line chunk |
| `tests.related_exclude` | only the folders that hold no offline test, for example `["tests/integration/**"]`; a folder that mixes offline tests with real-model ones stays in (the marker deselects the real-model ones), or `related` loses coverage |

## Structure enforcement
No mainstream Python linter counts function lines, so the installer writes `tests/test_architecture.py`, an AST test with shrink-only allowlists, as the source repository did:
- functions over 80 lines and classes over 300 lines (`ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`, `end_lineno - lineno + 1`);
- `nonlocal` statements (AR05);
- classes with more than one base defined in `src` (AR04);
- import direction between features (AR09): parse `ast.Import` and `ast.ImportFrom`, map each to its feature, forbid the directions in `docs/code-structure.md`. `import-linter` (`lint-imports` with layers and independence contracts) is the alternative when the team prefers configuration.
Proxies worth adding to ruff: `C901` (complexity) and `PLR0915` (statements).

| Rule | Tool | Baseline |
|---|---|---|
| AR24 complexity | ruff `C901` (`max-complexity = 10`), `PLR0913` (`max-args = 7`), `PLR1702` (`max-nested-blocks = 4`, preview) | `per-file-ignores` listing offenders, shrink-only |
| AR25 dead code | `vulture src --min-confidence 80` with a whitelist file for framework-reached symbols | the whitelist, shrink-only |
| AR26 duplicates | `jscpd --min-lines 10 src` (or PMD CPD) | `jscpd` report of today, new duplicates fail |
| AR27 typing | `mypy` `strict` is global-only; per module, list individual flags (`disallow_untyped_defs`, `disallow_incomplete_defs`, `warn_return_any` and similar) under `[[tool.mypy.overrides]] module = "pkg.x"`, add modules as they pass; or pyright `strict = [...]` | modules not yet covered are listed, only shrink (ratcheted by module list) |
| AR22 dispatch | ruff `B009`, `B010` (constant `getattr` and `setattr`) do not catch computed names: review `getattr(`, `importlib.import_module(`, `globals()[` | review |

## Offline guard
An autouse fixture in the **root** `conftest.py` blocks `socket.socket.connect` outside loopback; under the offline flag it also blocks loopback and database driver connects, and fails instead of skipping. The integration tier's session fixtures never load in the offline target because it ignores that path.

The guarantee belongs in the runner, not in the wrapper (TS55). Root `conftest.py`:
- unless `<PROJECT>_TEST_TIER` is `integration`: `os.environ["<PROJECT>_OFFLINE_ONLY"] = "1"` and `os.environ.pop("<PROJECT>_TEST_DATABASE_URL", None)` before any test module imports;
- `pytest_ignore_collect(collection_path, config)` returns `True` for the `tests/integration` folder unless that tier is named, so the integration fixtures never load;
- `commands.offline_args` can then be empty and a bare `uv run pytest <files>` is offline by construction; `gates.sh offline` keeps passing the same environment, and a canary test still executes it on one file (TS21).

Speed: coverage (`pytest-cov`) runs only on the whole offline suite and in CI: keep `--cov` out of `addopts` (or give single-file runs `--no-cov`), because a single file never meets the threshold and coverage tracing alone cost about 10 s on a 5-test file. Measure the runner's startup with `pytest --collect-only -q <file>` and `-p no:<plugin>` in `addopts` for each plugin nothing uses (look up the entry-point names with `pytest --trace-config`). A fresh worktree pays a cold venv sync and a cold bytecode cache: see `rules/07-workflow.md` (long-lived lanes).

Per-test timeout, one config line: `timeout = 60` under `[tool.pytest.ini_options]` (needs `pytest-timeout` in the dev dependencies; look up the current option name).

## Containers
When the repository uses Docker (a `Dockerfile`, a compose file, `testcontainers` in dependencies), the installer adds the `docker` section to `ai-kit.json` and wires TS27 to TS36:
- `tests/integration/conftest.py`: a session-scoped autouse fixture imports `sweep` and `load_labels` from `scripts.docker_hygiene` and sweeps stale leftovers when the session starts and when it ends (skipped under the offline flag); the fixture that builds images calls `check_disk`, `check_image_cap` and `check_total_images` first and fails the session when one refuses.
- Testcontainers: the root `conftest.py` patches `DockerContainer.start` to add the test labels, and fails the session when `TESTCONTAINERS_RYUK_DISABLED` is true (Ryuk reaps containers of a killed run).
- Compose: the label anchor is `<namespace>.purpose: ${<PROJECT>_PURPOSE:-dev}`; a stack fixture sets it to `test` and tears down with `down -v --remove-orphans`, failing when `down` fails.
- A test that runs `scripts/gates.sh` finds Git Bash on Windows (skip `System32` and `WindowsApps`, fall back to `<git>/../bin/bash.exe`).

## CI setup
```yaml
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies (locked)
        run: uv sync --frozen
```

## Ignore
`**/.venv/**`, `**/__pycache__/**`, `**/.mypy_cache/**`, `**/.pytest_cache/**`, `**/.ruff_cache/**`, `uv.lock`, `.coverage`.

## Layout
| Layout | Declare |
|---|---|
| Feature folders (`src/features/<f>/`) | `layout: "Feature folders under src/features"`, `feature_root` |
| Django: one app per domain (`<app>/models.py`, `views.py`, `urls.py`, `migrations/`) | `layout: "Django, one app per domain plus the project package"`, `areas: {"<app>": ["<app>/**"]}`, `map_dirs` for the project package |
| FastAPI or Flask by layer (`routers/`, `services/`, `models/`, `schemas/`) | `layout: "Folders by technical role (routers, services, models, schemas); product areas spread across them"`, `areas` one per PRD area with the globs of its files in each layer (`**/orders*.py`), `map_dirs: ["app/routers", "app/services", "app/models"]` |
| src layout package with subpackages | `layout: "src layout package with one subpackage per domain"`, one area per subpackage |

## Test naming
- `tests.mirror_patterns`: `["test_{name}"]` (also `{name}_test` when the project uses it); `tests.match_symbol: false`.
- Tests live in `tests/` mirroring the source tree, or beside the area in `<area>/tests/` (AR10). A test class imported into another test module gets a `_` alias so pytest does not collect it twice.
- `tests.junit_xml`: `reports/junit.xml`, and the runner gets `--junitxml=reports/junit.xml`.

## Generated files
`generated_patterns`: `**/*_pb2.py`, `**/*_pb2_grpc.py`, `**/migrations/0*.py` (Django, when auto-made), `**/_version.py`. Marker: protoc writes `# Generated by the protocol buffer compiler.  DO NOT EDIT!`; Django migrations write `# Generated by Django`; both match the ratchet's default marker regex; a generator whose header matches none sets `generated_marker` in `ai-kit.json`.

## Framework exemptions
- `unique_name_exempt`: `__init__.py`, `conftest.py`, `models.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tasks.py`, `settings.py`, `__main__.py`.
- AR04: Django `models.Model`, `forms.Form`, `admin.ModelAdmin`, DRF `serializers.Serializer`, pydantic `BaseModel`, SQLAlchemy `DeclarativeBase`, `Enum`, `TypedDict`, `Protocol`, and mixins the framework documents are allowed.
- AR05: module-level state behind `contextvars`, Django settings, FastAPI `Depends` providers count as explicit.

## Snapshots
Agents never run `pytest --snapshot-update` (syrupy), `--force-regen` (pytest-regressions) or `--inline-snapshot=fix,create` (inline-snapshot). Globs: `**/__snapshots__/**`, `**/*.ambr`, `tests/**/expected/**`.

## Contracts
- FastAPI: `python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True))"` into `docs/contracts/openapi.json`.
- Django: `python manage.py spectacular` (drf-spectacular) for the API; the schema from `python manage.py sqlmigrate` is per migration, so prefer `pg_dump --schema-only` (look up the project's database) for the schema snapshot.
- SQLAlchemy with Alembic: look up the offline SQL range syntax (`alembic upgrade <base>:head --sql`) to print the DDL.

## Setup
`commands.setup`: `uv sync --frozen` (uv), `poetry install --no-interaction` (Poetry), `python -m venv .venv && .venv/bin/pip install -r requirements.txt` (pip); add `pre-commit install` when the project uses it.

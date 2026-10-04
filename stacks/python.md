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
| `tests.runner` | `uv run pytest {files} --no-cov -q` |
| `tests.native_related` | empty (use `scripts/related_tests.py`) |
| `tests.failure_regex` | `^(?:FAILED\|ERROR)\s+(\S+)` (pytest's short summary) |

## Structure enforcement
No mainstream Python linter counts function lines, so the installer writes `tests/test_architecture.py`, an AST test with shrink-only allowlists, as the source repository did:
- functions over 80 lines and classes over 300 lines (`ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`, `end_lineno - lineno + 1`);
- `nonlocal` statements (AR05);
- classes with more than one base defined in `src` (AR04);
- import direction between features (AR09): parse `ast.Import` and `ast.ImportFrom`, map each to its feature, forbid the directions in `docs/code-structure.md`. `import-linter` (`lint-imports` with layers and independence contracts) is the alternative when the team prefers configuration.
Proxies worth adding to ruff: `C901` (complexity) and `PLR0915` (statements).

## Offline guard
An autouse fixture in the **root** `conftest.py` blocks `socket.socket.connect` outside loopback; under the offline flag it also blocks loopback and database driver connects, and fails instead of skipping. The integration tier's session fixtures never load in the offline target because it ignores that path.

## CI setup
```yaml
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies (locked)
        run: uv sync --frozen
```

## Ignore
`**/.venv/**`, `**/__pycache__/**`, `**/.mypy_cache/**`, `**/.pytest_cache/**`, `**/.ruff_cache/**`, `uv.lock`, `.coverage`.

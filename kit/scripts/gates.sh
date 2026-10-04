#!/usr/bin/env bash
# The gates, as commands rather than as things to remember.
#
# The offline target sets its own environment. The guarantee must not rest on
# somebody arranging their shell: a leaked database variable once turned the
# "offline" number into the full number, and two equal numbers looked like
# confirmation. The safe path is the invoked one.
set -euo pipefail

# ---- Fill these at setup (SETUP.md step 4). Keep them stack commands only. ----
TEST_CMD="${TEST_CMD:-<test runner, for example: uv run pytest>}"
OFFLINE_ARGS="${OFFLINE_ARGS:-<args that exclude the integration tier, for example: --ignore=tests/integration>}"
INTEGRATION_ARGS="${INTEGRATION_ARGS:-<args for the integration tier, for example: tests/integration>}"
LINT_CMD="${LINT_CMD:-<verify only, for example: ruff check . && ruff format --check . && mypy src>}"
FIX_CMD="${FIX_CMD:-<repair, for example: ruff check --fix . && ruff format .>}"
OFFLINE_UNSET=(${OFFLINE_UNSET:-DATABASE_URL})
OFFLINE_FLAG="${OFFLINE_FLAG:-OFFLINE_ONLY}"
LOG_DIR=".claude/prd-gate/state/_tests"
# -------------------------------------------------------------------------------

usage() {
    cat >&2 <<'USAGE'
usage: scripts/gates.sh <target> [args]

  related [files]  the tests related to the change (mirror + importers), plus the ratchet
  one <file>       one test file, offline, no coverage threshold
  offline          the whole unit tier with NO network and NO database: once, at the end
  integration      the integration tier (needs a database)
  full             everything; refuses to pass if the integration tier did not run
  baseline         run offline and record its failures as the baseline of a slug
  compare <slug>   run offline and print only failures that are not in the slug's baseline
  lint             verify lint, format and types, as CI does
  fix              repair lint and format; then run lint
  ratchet          structure ratchet (docs/code-structure.md)
  docs             the prd-gate docs gate
USAGE
    exit 2
}

offline_env() {
    local args=()
    for v in "${OFFLINE_UNSET[@]}"; do args+=(-u "$v"); done
    env "${args[@]}" "$OFFLINE_FLAG=1" "$@"
}

[ $# -ge 1 ] || usage
target="$1"
shift
mkdir -p "$LOG_DIR"

case "$target" in
related)
    python scripts/ratchet.py
    offline_env python scripts/related_tests.py "$@" --run
    ;;
one)
    offline_env $TEST_CMD $OFFLINE_ARGS "$@"
    ;;
offline)
    offline_env $TEST_CMD $OFFLINE_ARGS "$@"
    ;;
integration)
    $TEST_CMD $INTEGRATION_ARGS "$@"
    ;;
full)
    $TEST_CMD "$@"
    ;;
baseline)
    slug="${1:?usage: gates.sh baseline <slug>}"
    dir=".claude/prd-gate/state/$slug"
    mkdir -p "$dir"
    offline_env $TEST_CMD $OFFLINE_ARGS > "$dir/baseline.log" 2>&1 || true
    python scripts/new_failures.py --extract "$dir/baseline.log" > "$dir/baseline-failures.txt"
    wc -l < "$dir/baseline-failures.txt" | xargs echo "baseline failures:"
    ;;
compare)
    slug="${1:?usage: gates.sh compare <slug>}"
    dir=".claude/prd-gate/state/$slug"
    offline_env $TEST_CMD $OFFLINE_ARGS > "$dir/final.log" 2>&1 || true
    tail -n 1 "$dir/final.log"
    python scripts/new_failures.py "$dir/baseline-failures.txt" "$dir/final.log"
    ;;
lint)
    bash -c "$LINT_CMD"
    ;;
fix)
    bash -c "$FIX_CMD"
    ;;
ratchet)
    python scripts/ratchet.py "$@"
    ;;
docs)
    python .claude/skills/prd-gate/scripts/gate.py "$@"
    ;;
*)
    usage
    ;;
esac

#!/usr/bin/env bash
# The gates, as commands rather than as things to remember. Stack commands live
# in ai-kit.json ("commands"); this file is the same in every repository.
#
# The offline target sets its own environment. The guarantee must not rest on
# somebody arranging their shell: a leaked database variable once turned the
# "offline" number into the full number, and two equal numbers looked like
# confirmation. The safe path is the invoked one.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
LOG_DIR=".claude/prd-gate/state/_tests"

usage() {
    cat >&2 <<'USAGE'
usage: scripts/gates.sh <target> [args]

  related [files]  the ratchet, then the tests related to the change (mirror + importers)
  one <file>       one test file, offline, no coverage threshold
  offline          the whole unit tier with NO network and NO database: once, at the end
  integration      the integration tier (needs a database)
  full             everything
  baseline <slug>  run offline and record its failures as the slug's baseline
  compare <slug>   run offline and print only failures that are not in the baseline
  lint             verify lint, format and types, as CI does
  fix              repair lint and format; then run lint
  imports          the import check (catches cycles)
  ratchet          structure ratchet (docs/code-structure.md)
  docs [args]      the prd-gate docs gate
USAGE
    exit 2
}

cmd() {
    python - "$1" <<'PY'
import json, sys
value = json.load(open("ai-kit.json", encoding="utf-8"))["commands"][sys.argv[1]]
print(" ".join(value) if isinstance(value, list) else value)
PY
}

offline() {
    local args=()
    for v in $(cmd offline_unset); do args+=(-u "$v"); done
    env "${args[@]}" "$(cmd offline_flag)=1" bash -c "$*"
}

[ $# -ge 1 ] || usage
target="$1"
shift
mkdir -p "$LOG_DIR"

case "$target" in
related)
    python scripts/ratchet.py
    offline "python scripts/related_tests.py $* --run"
    ;;
one)
    offline "$(cmd test) $(cmd offline_args) $(cmd no_coverage_args) $*"
    ;;
offline)
    offline "$(cmd test) $(cmd offline_args) $*"
    ;;
integration)
    bash -c "$(cmd test) $(cmd integration_args) $*"
    ;;
full)
    bash -c "$(cmd test) $*"
    ;;
baseline)
    slug="${1:?usage: gates.sh baseline <slug>}"
    dir=".claude/prd-gate/state/$slug"
    mkdir -p "$dir"
    offline "$(cmd test) $(cmd offline_args)" > "$dir/baseline.log" 2>&1 || true
    python scripts/new_failures.py --extract "$dir/baseline.log" > "$dir/baseline-failures.txt"
    echo "baseline failures: $(wc -l < "$dir/baseline-failures.txt") (log: $dir/baseline.log)"
    ;;
compare)
    slug="${1:?usage: gates.sh compare <slug>}"
    dir=".claude/prd-gate/state/$slug"
    mkdir -p "$dir"
    offline "$(cmd test) $(cmd offline_args)" > "$dir/final.log" 2>&1 || true
    tail -n 1 "$dir/final.log"
    python scripts/new_failures.py "$dir/baseline-failures.txt" "$dir/final.log"
    ;;
lint)
    bash -c "$(cmd lint)"
    ;;
fix)
    bash -c "$(cmd fix)"
    ;;
imports)
    bash -c "$(cmd import_check)"
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

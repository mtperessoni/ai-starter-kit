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
  integration      the integration tier (needs Docker): guards first; on exit, even a failed or
                   interrupted one: sweep, build cache bounded, old task outputs deleted
  full             everything: same guards, same exit cleanup
  build [args]     docker compose build: same guards, same exit cleanup
  guard            disk, image-cap and Docker disk file guards (guard-disk, guard-images run one each)
  sweep            remove this repo's test containers, volumes and networks older than
                   DOCKER_STALE_MINUTES (60): what a killed run left behind
  docker-clean     remove labelled leftovers of any age and report unlabelled images (never touches those)
  clean-outputs    delete Claude Code task outputs older than 2 days or over 200 MB
  baseline <slug>  run offline and record its failures as the slug's baseline
  compare <slug>   run offline and print only failures that are not in the baseline
  lint             verify lint, format and types, as CI does
  fix              repair lint and format; then run lint
  imports          the import check (catches cycles)
  ratchet          structure ratchet (docs/code-structure.md)
  docs [args]      the prd-gate docs gate
  context <name>   name the run context (.ai-kit/runs/current) for the telemetry
  retro [args]     the run retrospective (scripts/retro.py): --context <name>, --prune
  setup            make a fresh clone or worktree ready to test (commands.setup)
  hotspots [args]  code files ranked by commits x lines: what the readiness plan splits first
  contracts        schema and API snapshots (ai-kit.json "contracts") still match the code

With scripts/gates.project.sh present, any other target, and every target in ai-kit.json
commands.project_targets, runs there with its arguments.
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

# Every test and build target runs through the probe: same output, same exit code, plus one resources line.
probe() {
    local label="$1"
    shift
    python scripts/run_probe.py --label "$label" -- "$@"
}

offline() {
    local label="$1" args=()
    shift
    for v in $(cmd offline_unset); do args+=(-u "$v"); done
    env "${args[@]}" "$(cmd offline_flag)=1" python scripts/run_probe.py --label "$label" -- bash -c "$*"
}

# Limits (env, defaults in scripts/docker_hygiene.py): MIN_FREE_GB 10, IMAGE_CAP 8, IMAGE_CAP_GB 6,
# TOTAL_IMAGE_CAP_GB 20, BUILD_CACHE_MAX_GB 3, DOCKER_STALE_MINUTES 60, DOCKER_DISK_WARN_GB 40.
# GATES_FREE_GB_OVERRIDE and DOCKER_CLI are for tests.
read -ra DOCKER <<< "${DOCKER_CLI:-docker}"
guard_disk() { python scripts/docker_hygiene.py check-disk; }
guard_images() { python scripts/docker_hygiene.py check-image-cap; }
guards() {
    guard_disk
    guard_images
    python scripts/docker_hygiene.py check-docker-disk
}
prune_cache() { python scripts/docker_hygiene.py prune-cache || echo "build cache prune failed, continuing" >&2; }
sweep() { python scripts/docker_hygiene.py sweep || echo "sweep failed, continuing" >&2; }
# Runs on every exit of a Docker target, failed or interrupted, so a broken run never leaves the disk to fill.
after_docker() {
    sweep
    prune_cache
    python scripts/clean_task_outputs.py || echo "clean-outputs failed, continuing" >&2
}

[ $# -ge 1 ] || usage
target="$1"
shift
mkdir -p "$LOG_DIR"

PROJECT_GATES="scripts/gates.project.sh"
delegate() { exec bash "$PROJECT_GATES" "$target" "$@"; }
# commands.project_targets: targets the project keeps even when this file defines them.
if [ -f "$PROJECT_GATES" ] && python - "$target" <<'PY'
import json, sys
listed = json.load(open("ai-kit.json", encoding="utf-8")).get("commands", {}).get("project_targets", [])
sys.exit(0 if sys.argv[1] in listed else 1)
PY
then
    delegate "$@"
fi

case "$target" in
related)
    python scripts/ratchet.py
    offline related "python scripts/related_tests.py $* --run"
    ;;
one)
    offline one "$(cmd test) $(cmd offline_args) $(cmd no_coverage_args) $*"
    ;;
offline)
    offline offline "$(cmd test) $(cmd offline_args) $*"
    ;;
integration)
    guards
    trap after_docker EXIT
    probe integration bash -c "$(cmd test) $(cmd integration_args) $*"
    ;;
full)
    guards
    trap after_docker EXIT
    probe full bash -c "$(cmd test) $*"
    ;;
build)
    guards
    trap after_docker EXIT
    probe build "${DOCKER[@]}" compose build "$@"
    ;;
guard)
    guards
    ;;
sweep)
    sweep
    ;;
guard-disk)
    guard_disk
    ;;
guard-images)
    guard_images
    ;;
prune-cache)
    prune_cache
    ;;
docker-clean)
    python scripts/docker_hygiene.py clean
    ;;
clean-outputs)
    python scripts/clean_task_outputs.py "$@"
    ;;
baseline)
    slug="${1:?usage: gates.sh baseline <slug>}"
    dir=".claude/prd-gate/state/$slug"
    mkdir -p "$dir"
    offline offline "$(cmd test) $(cmd offline_args)" > "$dir/baseline.log" 2>&1 || true
    python scripts/new_failures.py --extract "$dir/baseline.log" > "$dir/baseline-failures.txt"
    echo "baseline failures: $(wc -l < "$dir/baseline-failures.txt") (log: $dir/baseline.log)"
    ;;
compare)
    slug="${1:?usage: gates.sh compare <slug>}"
    dir=".claude/prd-gate/state/$slug"
    mkdir -p "$dir"
    offline offline "$(cmd test) $(cmd offline_args)" > "$dir/final.log" 2>&1 || true
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
context)
    name="${1:?usage: gates.sh context <name>}"
    mkdir -p .ai-kit/runs
    printf '%s
' "$name" > .ai-kit/runs/current
    ;;
retro)
    python scripts/retro.py "$@"
    ;;
docs)
    python .claude/skills/prd-gate/scripts/gate.py "$@"
    ;;
setup)
    setup_cmd="$(python -c 'import json; print(json.load(open("ai-kit.json", encoding="utf-8"))["commands"].get("setup", ""))')"
    case "$setup_cmd" in
    "" | "<"*) echo "commands.setup is not set in ai-kit.json" >&2; exit 2 ;;
    esac
    bash -c "$setup_cmd"
    ;;
hotspots)
    python scripts/hotspots.py "$@"
    ;;
contracts)
    python scripts/contract_drift.py
    ;;
*)
    [ -f "$PROJECT_GATES" ] && delegate "$@"
    usage
    ;;
esac

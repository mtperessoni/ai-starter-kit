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
LOG_DIR=".claude/prd-flow/state/_tests"
GATE_PY=".claude/skills/prd-flow/scripts/gate.py"

usage() {
    cat >&2 <<'USAGE'
usage: scripts/gates.sh <target> [args]

  related [files]  the ratchet, then the tests related to the change (mirror + importers)
  one <file>       one test file, offline, no coverage threshold
  red <test>       one test, offline, expected to fail: prints "Red: <exit code>" (exit 0 only when it failed)
  offline          the whole unit tier with NO network and NO database: once, at the end
  integration      the integration tier (needs Docker): guards first; on exit, even a failed or
                   interrupted one: sweep, build cache bounded, old task outputs deleted
  full             everything: same guards, same exit cleanup
  build [args]     docker compose build: same guards, same exit cleanup
  guard            disk, image-cap and Docker disk file guards (guard-disk, guard-images run one each)
  sweep            remove this repo's test containers, volumes and networks older than
                   DOCKER_STALE_MINUTES (60): what a killed run left behind
  docker-clean     remove labelled leftovers of any age and report unlabelled images (never touches those)
  clean-outputs    delete Claude Code task outputs older than 2 days or over 200 MB (any over 500 MB, in any project)
  baseline <slug> [--bg] [--commit REF]
                   the offline failures at a commit (default HEAD), run in a throwaway worktree, cached by commit plus lockfile,
                   with a lock and a no-progress watchdog; tests.baseline_deselect is skipped; run it as a background Bash (completion event);
                   --bg (detached, no event) is kept for compatibility, not recommended
  compare <slug>   run offline and print only failures that are not in the baseline
  rerun <slug> <id>...  rerun only those failing ids against the baseline (the close step does it for a fresh full run)
  verify <slug> [--since REF]
                   one verification per wave or batch: related tests of every file changed since the ref (default: the last verification,
                   else the plan commit, else the base branch), the structure tests and the docs gate; log, short summary and
                   verify.stamp; a rerun with nothing changed reruns only what failed
  reap [--older-than <min>] [--dry-run]
                   kill, by PID tree, this session's stdin-waiting or older-than-N-minutes (default 20) processes; never a baseline|compare|verify tree;
                   prints "reaped: <n>" and "left: 0" or the survivors
  python           print the resolved interpreter (the one every target uses)
  lint             verify lint, format and types, as CI does; one line: lint ok, or lint FAILED (exit N), log <path>
  fix              repair lint and format; same one-line result (then run lint)
  imports          the import check (catches cycles); same one-line result
  ratchet          structure ratchet (docs/code-structure.md)
  docs [slug|args] the prd-flow docs gate; a slug runs every check of the change in one process (gate.py --docs)
  html [args]      rebuild the PRD and TRD HTML pages (build_prd_html.py, build_trd_html.py); --check verifies both
  close [slug]     the closing ceremony in one block (retro findings and failure lines included): compare against the baseline
                   (a fresh full run of this commit is reused), lint, trailers, docs --final, retro; full log in
                   .claude/prd-flow/state/_close/<slug>.log; exit 1 on a failure
  trailers [range] commits touching the source folders carry Rules: or Case: none (default origin/<base>..HEAD)
  context <name>   name the run context (.ai-kit/runs/current) for the telemetry
  retro [args]     the run retrospective (scripts/retro.py): --context <name>, --prune
  setup            make a fresh clone or worktree ready to test (commands.setup)
  hotspots [args]  code files ranked by commits x lines: what the readiness plan splits first
  contracts        schema and API snapshots (ai-kit.json "contracts") still match the code

The interpreter is resolved once: GATES_PYTHON, then commands.python in ai-kit.json, then python3 and python on PATH;
the Windows Store stub is rejected.
With scripts/gates.project.sh present, any other target, and every target in ai-kit.json
commands.project_targets, runs there with its arguments.
USAGE
    exit 2
}

PY_WHY=""
python_ok() {
    local candidate="$1" out
    case "$candidate" in
    *[Ww]indows[Aa]pps*) PY_WHY="$candidate is the Windows Store stub (WindowsApps)"; return 1 ;;
    esac
    out="$("$candidate" -c 'import sys; print(sys.version_info[0])' 2>&1)" || { PY_WHY="$candidate is not a usable Python 3"; return 1; }
    case "$out" in
    *"was not found"* | *"não foi encontrado"*) PY_WHY="$candidate is not a usable Python 3 (store stub text)"; return 1 ;;
    esac
    [ "$out" = "3" ] || { PY_WHY="$candidate is not a usable Python 3"; return 1; }
}

resolve_python() {
    local candidate configured="" found
    if [ -n "${GATES_PYTHON:-}" ]; then
        python_ok "$GATES_PYTHON" || { echo "gates.sh: GATES_PYTHON: $PY_WHY" >&2; return 1; }
        printf '%s' "$GATES_PYTHON"
        return 0
    fi
    [ -f ai-kit.json ] && configured="$(sed -n 's/.*"python"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' ai-kit.json | head -n 1)"
    case "$configured" in
    "" | "<"*) ;;
    *)
        python_ok "$configured" || { echo "gates.sh: commands.python: $PY_WHY" >&2; return 1; }
        printf '%s' "$configured"
        return 0
        ;;
    esac
    for found in python3 python; do
        while IFS= read -r candidate; do
            if python_ok "$candidate"; then
                printf '%s' "$candidate"
                return 0
            fi
        done < <(type -ap "$found" 2>/dev/null || true)
    done
    echo "gates.sh: no usable Python 3 on PATH (the Windows Store stub is rejected); set GATES_PYTHON or commands.python in ai-kit.json" >&2
    return 1
}

cmd() {
    "$PY" scripts/config_get.py "commands.$1"
}

gate_has() {
    local help
    help="$("$PY" -B "$GATE_PY" --help 2>&1 || true)"
    case "$help" in *"$1"*) return 0 ;; esac
    return 1
}

# One result line per check; the output goes to the log so a proxy that swallows output cannot hide the verdict.
checked() {
    local name="$1" log="$LOG_DIR/$1.log" code=0
    bash -c "$2" > "$log" 2>&1 || code=$?
    if [ "$code" -eq 0 ]; then echo "$name ok"; else echo "$name FAILED (exit $code), log $log"; fi
    return "$code"
}

# Every test and build target runs through the probe: same output, same exit code, plus one resources line.
probe() {
    local label="$1"
    shift
    "$PY" scripts/run_probe.py --label "$label" -- "$@"
}

# offline <label> <argv...>: the argv runs as given, with the offline environment; no shell sees it.
offline() {
    local label="$1" args=() v
    shift
    for v in $(cmd offline_unset); do args+=(-u "$v"); done
    env "${args[@]}" "$(cmd offline_flag)=1" "$PY" scripts/run_probe.py --label "$label" -- "$@"
}

# offline_sh <label> <configured command string> <args...>: the string is configuration; the args reach it quoted, as "$@".
offline_sh() {
    local label="$1" line="$2"
    shift 2
    offline "$label" bash -c "$line \"\$@\"" bash "$@"
}

# Limits (env, defaults in scripts/docker_hygiene.py): MIN_FREE_GB 10, IMAGE_CAP 8, IMAGE_CAP_GB 6,
# TOTAL_IMAGE_CAP_GB 20, BUILD_CACHE_MAX_GB 3, DOCKER_STALE_MINUTES 60, DOCKER_DISK_WARN_GB 40.
# GATES_FREE_GB_OVERRIDE and DOCKER_CLI are for tests.
read -ra DOCKER <<< "${DOCKER_CLI:-docker}"
guard_disk() { "$PY" scripts/docker_hygiene.py check-disk; }
guard_images() { "$PY" scripts/docker_hygiene.py check-image-cap; }
guards() {
    guard_disk
    guard_images
    "$PY" scripts/docker_hygiene.py check-docker-disk
}
prune_cache() { "$PY" scripts/docker_hygiene.py prune-cache || echo "build cache prune failed, continuing" >&2; }
sweep() { "$PY" scripts/docker_hygiene.py sweep || echo "sweep failed, continuing" >&2; }
# Runs on every exit of a Docker target, failed or interrupted, so a broken run never leaves the disk to fill.
after_docker() {
    sweep
    prune_cache
    "$PY" scripts/clean_task_outputs.py || echo "clean-outputs failed, continuing" >&2
}

[ $# -ge 1 ] || usage
target="$1"
shift
PY="$(resolve_python)" || exit 2
mkdir -p "$LOG_DIR"

PROJECT_GATES="scripts/gates.project.sh"
delegate() { exec bash "$PROJECT_GATES" "$target" "$@"; }
# commands.project_targets: targets the project keeps even when this file defines them.
if [ -f "$PROJECT_GATES" ] && "$PY" scripts/config_get.py --has commands.project_targets "$target"; then
    delegate "$@"
fi

case "$target" in
related)
    "$PY" scripts/ratchet.py
    args_file="$LOG_DIR/related.args"
    : > "$args_file"
    for file in "$@"; do printf '%s\n' "$file" >> "$args_file"; done
    related_help="$("$PY" scripts/related_tests.py --help 2>&1 || true)"
    case "$related_help" in
    *--args-file*) offline related "$PY" scripts/related_tests.py --args-file "$args_file" --run ;;
    *) offline related "$PY" scripts/related_tests.py "$@" --run ;;
    esac
    ;;
one)
    offline_sh one "$(cmd test) $(cmd offline_args) $(cmd no_coverage_args)" "$@"
    ;;
red)
    [ $# -ge 1 ] || { echo "usage: gates.sh red <test>" >&2; exit 2; }
    red_log="$LOG_DIR/red.log"
    red_code=0
    offline_sh red "$(cmd test) $(cmd offline_args) $(cmd no_coverage_args)" "$@" > "$red_log" 2>&1 || red_code=$?
    echo "Red: $red_code"
    echo "log: $red_log"
    [ "$red_code" -ne 0 ]
    ;;
offline)
    offline_sh offline "$(cmd test) $(cmd offline_args)" "$@"
    ;;
integration)
    guards
    trap after_docker EXIT
    probe integration bash -c "$(cmd test) $(cmd integration_args) \"\$@\"" bash "$@"
    ;;
full)
    guards
    trap after_docker EXIT
    probe full bash -c "$(cmd test) \"\$@\"" bash "$@"
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
    "$PY" scripts/docker_hygiene.py clean
    ;;
clean-outputs)
    "$PY" scripts/clean_task_outputs.py "$@"
    ;;
baseline)
    [ $# -ge 1 ] || { echo "usage: gates.sh baseline <slug> [--bg] [--commit REF]" >&2; exit 2; }
    GATES_BASH="$(cygpath -w "$BASH" 2>/dev/null || printf %s "$BASH")" "$PY" scripts/baseline.py "$@"
    ;;
verify)
    [ $# -ge 1 ] || { echo "usage: gates.sh verify <slug> [--since REF]" >&2; exit 2; }
    GATES_BASH="$(cygpath -w "$BASH" 2>/dev/null || printf %s "$BASH")" "$PY" scripts/verify.py "$@"
    ;;
reap)
    "$PY" scripts/reap.py "$@"
    ;;
python)
    echo "$PY"
    ;;
compare)
    slug="${1:?usage: gates.sh compare <slug>}"
    dir=".claude/prd-flow/state/$slug"
    mkdir -p "$dir"
    rm -f "$dir/final.stamp"
    offline_sh offline "$(cmd test) $(cmd offline_args) $("$PY" scripts/config_get.py --deselect)" > "$dir/final.log" 2>&1 || true
    "$PY" scripts/close_gate.py --stamp > "$dir/final.stamp"
    tail -n 1 "$dir/final.log"
    "$PY" scripts/new_failures.py "$dir/baseline-failures.txt" "$dir/final.log"
    ;;
rerun)
    slug="${1:?usage: gates.sh rerun <slug> <id>...}"
    shift
    dir=".claude/prd-flow/state/$slug"
    mkdir -p "$dir"
    rerun_code=0
    offline_sh offline "$(cmd test) $(cmd offline_args) $("$PY" scripts/config_get.py --deselect)" "$@" > "$dir/rerun.log" 2>&1 || rerun_code=$?
    tail -n 1 "$dir/rerun.log"
    new_code=0
    "$PY" scripts/new_failures.py "$dir/baseline-failures.txt" "$dir/rerun.log" || new_code=$?
    if [ "$rerun_code" -ne 0 ] && [ "$new_code" -eq 0 ]; then
        echo "rerun FAILED (exit $rerun_code): the runner failed without a failure line, log $dir/rerun.log"
        exit 1
    fi
    exit "$new_code"
    ;;
lint)
    checked lint "$(cmd lint)"
    ;;
fix)
    checked fix "$(cmd fix)"
    ;;
imports)
    checked imports "$(cmd import_check)"
    ;;
ratchet)
    "$PY" scripts/ratchet.py "$@"
    ;;
context)
    name="${1:?usage: gates.sh context <name>}"
    mkdir -p .ai-kit/runs
    printf '%s\n' "$name" > .ai-kit/runs/current
    ;;
retro)
    "$PY" scripts/retro.py "$@"
    ;;
docs)
    if [ $# -ge 1 ] && [[ "$1" != -* ]] && gate_has --docs; then
        "$PY" "$GATE_PY" --docs "$@"
    else
        "$PY" "$GATE_PY" "$@"
    fi
    ;;
html)
    html_rc=0
    "$PY" .claude/skills/prd-flow/scripts/build_prd_html.py "$@" || html_rc=1
    "$PY" .claude/skills/prd-flow/scripts/build_trd_html.py "$@" || html_rc=1
    exit "$html_rc"
    ;;
close)
    GATES_BASH="$(cygpath -w "$BASH" 2>/dev/null || printf %s "$BASH")" "$PY" scripts/close_gate.py "$@"
    ;;
setup)
    setup_cmd="$("$PY" scripts/config_get.py commands.setup "")"
    case "$setup_cmd" in
    "" | "<"*) echo "commands.setup is not set in ai-kit.json" >&2; exit 2 ;;
    esac
    bash -c "$setup_cmd"
    ;;
trailers)
    "$PY" scripts/commit_trailers.py "$@"
    ;;
hotspots)
    "$PY" scripts/hotspots.py "$@"
    ;;
contracts)
    "$PY" scripts/contract_drift.py
    ;;
*)
    [ -f "$PROJECT_GATES" ] && delegate "$@"
    usage
    ;;
esac

#!/usr/bin/env bash
# The gates, as commands rather than as things to remember. Stack commands live
# in ai-kit.json ("commands"); this file is the same in every repository.
#
# The offline target sets its own environment. The guarantee must not rest on
# somebody arranging their shell: a leaked database variable once turned the
# "offline" number into the full number, and two equal numbers looked like
# confirmation. The safe path is the invoked one.
set -euo pipefail
export PYTHONUTF8=1

cd "$(git rev-parse --show-toplevel)"
LOG_DIR=".claude/prd-flow/state/_tests"
GATE_PY=".claude/skills/prd-flow/scripts/gate.py"
SWEEP_PY=".claude/skills/prd-flow/scripts/prd_sweep.py"

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
  prd-sweep [args] the prd-flow sweep of conflicts and impact across every PRD (prd_sweep.py); exit 2 when the script is missing
  docker-clean     remove labelled leftovers of any age and report unlabelled images (never touches those)
  clean-outputs    delete Claude Code task outputs older than 2 days or over 200 MB (any over 500 MB, in any project)
  baseline <slug> [--bg] [--commit REF]
                   the offline failures at a commit (default HEAD), run in a throwaway worktree, cached by commit plus lockfile,
                   with a lock and a no-progress watchdog; tests.baseline_deselect is skipped; run it as a background Bash (completion event);
                   --bg (detached, no event) is kept for compatibility, not recommended
  compare <slug>   run offline and print only failures that are not in the baseline; fails when the run ends without its summary line;
                   a run of the same test content (source and test folders, lockfiles, dirty diff) is reused from state/_compare/<hash>
  rerun <slug> <id>...  rerun only those failing ids against the baseline (the close step does it for a fresh full run)
  verify <slug> [--since REF]
                   one verification per wave or batch: related tests of every file changed since the ref (default: the last verification,
                   else the plan commit, else the base branch), the structure tests and the docs gate; log, short summary and
                   verify.stamp; a rerun with nothing changed reruns only what failed
  reap [--older-than <min>] [--dry-run]
                   kill, by PID tree, this session's stdin-waiting or older-than-N-minutes (default 20) processes; never a baseline|compare|verify tree;
                   prints "reaped: <n>" and "left: 0" or the survivors; a baseline|compare|verify tree is spared only while its
                   state/<slug>/<target>.status says running and it is under 60 minutes old
  cleanup [slug] [--session-end] [--dry-run]
                   reap, delete this project's idle task outputs and loose files in .ai-kit/runs/, move state folders untouched for
                   7 days to state/_stale/, purge _stale/ after 14 days and _tests/_gate caches after 3; --session-end: reap and
                   task outputs only; at most 8 lines ending with "left: 0" or the survivors; exit 1 on a survivor
  watch <slug> [--minutes N]
                   the one bounded waiter per wave (default 30 min), run in the background by the chief: prints "stuck: <id> <type>
                   idle <n> min", "deadline: <ids>" or "done: no agent running"
  python           print the resolved interpreter (the one every target uses)
  lint             verify lint, format and types, as CI does; one line: lint ok, or lint FAILED (exit N), log <path>
  fix              repair lint and format; same one-line result (then run lint)
  fix-files <file>...   fix only those files (commands.fix_file with {files}, in chunks); unset runs fix with a note
  lint-files <file>...  lint only those files (commands.lint_file with {files}, in chunks); unset runs lint with a note
  move <source> <start> <end> <destination> [--at LINE]
                   move lines by script (scripts/move_lines.py, same arguments), never retyped
  settings-check   .claude/settings*.json deny rules that block files the flow writes (docs/prd, docs/trd, changes, state); exit 1 with the lines
  imports          the import check (catches cycles); same one-line result
  ratchet          structure ratchet (docs/code-structure.md)
  docs [slug|args] the prd-flow docs gate; a slug runs every check of the change in one process (gate.py --docs)
  html [args]      rebuild the PRD and TRD HTML pages (build_prd_html.py, build_trd_html.py); --check verifies both
  close [slug] [--case C2..C6]
                   the closing ceremony in one block (retro findings and failure lines included): lint, trailers, docs --final, then the
                   compare result against the baseline (read once, never run inline), retro; full log, written per step, in
                   .claude/prd-flow/state/_close/<slug>.log; exit 1 on a failure; --case C4 skips the compare and baseline steps
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
    configured="${configured//\\\\/\\}"
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

# The run keys, read in one Python process: CFG_TEST, CFG_OFFLINE_ARGS, CFG_FAST (tests.fast_flags, for example "--no-cov -n auto":
# added to baseline and compare only when the project declares them), CFG_UNSET, CFG_FLAG.
CFG_LOADED=0
CFG_TEST="" CFG_OFFLINE_ARGS="" CFG_FAST="" CFG_UNSET="" CFG_FLAG=""
load_run_config() {
    local line
    if [ "$CFG_LOADED" -eq 1 ]; then return 0; fi
    while IFS= read -r line; do
        line="${line%$'\r'}"
        case "$line" in
        commands.test=*) CFG_TEST="${line#*=}" ;;
        commands.offline_args=*) CFG_OFFLINE_ARGS="${line#*=}" ;;
        tests.fast_flags=*) CFG_FAST="${line#*=}" ;;
        commands.offline_unset=*) CFG_UNSET="${line#*=}" ;;
        commands.offline_flag=*) CFG_FLAG="${line#*=}" ;;
        esac
    done < <("$PY" scripts/config_get.py --many commands.test commands.offline_args tests.fast_flags commands.offline_unset commands.offline_flag)
    CFG_LOADED=1
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

# files_target <name> <fileKey> <wholeKey> <files...>: commands.<fileKey> with {files} on those files only, in chunks of
# 25 so a Windows command line stays short; unset (empty or a placeholder) falls back to commands.<wholeKey> with a note.
files_target() {
    local name="$1" key="$2" whole="$3" tpl line rest chunk n code=0 log="$LOG_DIR/$1.log"
    shift 3
    [ $# -ge 1 ] || { echo "usage: gates.sh $name <file>..." >&2; exit 2; }
    tpl="$("$PY" scripts/config_get.py "commands.$key" "")"
    case "$tpl" in
    "" | "<"*)
        echo "gates.sh: commands.$key is not set in ai-kit.json, running commands.$whole on the whole repository" >&2
        checked "$name" "$(cmd "$whole")"
        return
        ;;
    esac
    case "$tpl" in *'{files}'*) ;; *) tpl="$tpl {files}" ;; esac
    : > "$log"
    while [ $# -gt 0 ]; do
        chunk=""
        n=0
        while [ $# -gt 0 ] && [ "$n" -lt 25 ]; do
            chunk="$chunk $(printf '%q' "$1")"
            shift
            n=$((n + 1))
        done
        line=""
        rest="$tpl"
        while [[ "$rest" == *'{files}'* ]]; do
            line="$line${rest%%\{files\}*}$chunk"
            rest="${rest#*\{files\}}"
        done
        bash -c "$line$rest" >> "$log" 2>&1 || code=$?
    done
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
    load_run_config
    for v in $CFG_UNSET; do args+=(-u "$v"); done
    env "${args[@]}" "${CFG_FLAG:-OFFLINE_ONLY}=1" "$PY" scripts/run_probe.py --label "$label" -- "$@"
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
prd-sweep)
    [ -f "$SWEEP_PY" ] || { echo "gates.sh: $SWEEP_PY is missing" >&2; exit 2; }
    "$PY" "$SWEEP_PY" "$@"
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
    case "$1" in */* | *\\* | *..* | -*) echo "gates.sh: bad slug '$1'" >&2; exit 2 ;; esac
    verify_dir=".claude/prd-flow/state/$1"
    mkdir -p "$verify_dir"
    printf 'running\n' > "$verify_dir/verify.status"
    trap 'printf "done\n" > "$verify_dir/verify.status"' EXIT
    verify_code=0
    GATES_BASH="$(cygpath -w "$BASH" 2>/dev/null || printf %s "$BASH")" "$PY" scripts/verify.py "$@" || verify_code=$?
    exit "$verify_code"
    ;;
reap)
    "$PY" scripts/reap.py "$@"
    ;;
cleanup)
    "$PY" scripts/cleanup.py "$@"
    ;;
watch)
    [ $# -ge 1 ] || { echo "usage: gates.sh watch <slug> [--minutes N] [--since <epoch>]" >&2; exit 2; }
    "$PY" scripts/watch.py "$@"
    ;;
python)
    echo "$PY"
    ;;
compare)
    slug="${1:?usage: gates.sh compare <slug>}"
    dir=".claude/prd-flow/state/$slug"
    mkdir -p "$dir"
    rm -f "$dir/final.stamp" "$dir/exit"
    "$PY" scripts/close_gate.py --stamp > "$dir/final.stamp.pending"
    content="$("$PY" scripts/close_gate.py --hash)"
    cache=".claude/prd-flow/state/_compare/$content"
    compare_code=0
    load_run_config
    if [ -f "$cache/final.log" ] && [ -f "$cache/exit" ]; then
        cp "$cache/final.log" "$dir/final.log"
        compare_code="$(cat "$cache/exit")"
        echo "compare: reused the full run of the same test content ${content:0:12}"
    else
        printf 'running\n' > "$dir/compare.status"
        trap 'printf "done\n" > "$dir/compare.status"' EXIT
        offline_sh offline "$CFG_TEST $CFG_OFFLINE_ARGS $CFG_FAST $("$PY" scripts/config_get.py --deselect)" > "$dir/final.log" 2>&1 || compare_code=$?
        if "$PY" scripts/new_failures.py --require-summary "$dir/final.log" > /dev/null; then
            mkdir -p "$cache"
            printf '%s\n' "$compare_code" > "$cache/exit"
            cp "$dir/final.log" "$cache/final.log.tmp"
            mv -f "$cache/final.log.tmp" "$cache/final.log"
        fi
    fi
    printf '%s\n' "$compare_code" > "$dir/exit"
    mv -f "$dir/final.stamp.pending" "$dir/final.stamp"
    tail -n 1 "$dir/final.log"
    if ! "$PY" scripts/new_failures.py --require-summary "$dir/final.log" > /dev/null; then
        echo "compare FAILED: suite ended without its summary line (runner exit $compare_code), log $dir/final.log"
        exit 1
    fi
    "$PY" scripts/new_failures.py --exit-code "$compare_code" "$dir/baseline-failures.txt" "$dir/final.log"
    ;;
rerun)
    slug="${1:?usage: gates.sh rerun <slug> <id>...}"
    shift
    dir=".claude/prd-flow/state/$slug"
    mkdir -p "$dir"
    rerun_code=0
    load_run_config
    rm -f "$dir/rerun.exit"
    offline_sh offline "$CFG_TEST $CFG_OFFLINE_ARGS $("$PY" scripts/config_get.py --deselect)" "$@" > "$dir/rerun.log" 2>&1 || rerun_code=$?
    printf '%s\n' "$rerun_code" > "$dir/rerun.exit"
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
fix-files)
    files_target fix-files fix_file fix "$@"
    ;;
lint-files)
    files_target lint-files lint_file lint "$@"
    ;;
move)
    "$PY" scripts/move_lines.py "$@"
    ;;
settings-check)
    "$PY" scripts/settings_check.py "$@"
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

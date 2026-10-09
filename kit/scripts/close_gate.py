"""Closing ceremony in one call: the full suite against the baseline, lint, trailers, the final gate, retro.

Usage: python scripts/close_gate.py [slug] [--case C2..C6]     (through scripts/gates.sh close [slug] [--case C])
Runs `gates.sh cleanup <slug>` as the last step after retro (one line, or the survivors; it never fails the close).
With --case C4 the compare and baseline steps are skipped and say so (no code change to prove); without --case nothing changes.
Close never runs tests: with tests.rerun_ids it prints the failing ids to rerun (gates.sh rerun) and fails; every subprocess has a timeout.
The baseline counts only with baseline.status ok (or watchdog); a compare result counts only with the runner exit code stored beside its log,
and an exit other than 0 with no recognized failure line is not a pass.
Prints one block of at most 24 lines, every failure with `owner:` and `next:` lines (a missing baseline or a trailer that needs a history rewrite is `owner: user`) (the retro findings, at most 5, highest severity first; a failing check's last lines, at most 10); the full output of every step goes to .claude/prd-flow/state/_close/<slug>.log.
Refuses uncommitted tracked changes under docs/ and changes/ (promote's output, exit 1, after the baseline check); any other modified tracked file is a note line only.
Prints "already closed" (exit 0) only when the state is gone, changes/archive/<NNN>-<slug> exists and git log has "docs(prd): promote <slug>".
Order: lint, trailers, docs --final (fast), then the compare result, then retro. The log is appended per step, so a killed close leaves what ran.
The compare step never runs the suite and never waits: it reads, once, the result of a full run of this tree (state/<slug>/final.stamp equals HEAD plus the content of every tracked change and untracked file) or of the same test content (state/_compare/<hash>, a hash of the source and test folders, lockfiles and dirty diff, so a docs-only commit reuses it). New failing ids are rerun alone (gates.sh rerun) when tests.rerun_ids is true. No result, or one still running, is a failed step that names the background compare to start. A result without its summary line fails.
A baseline still running (baseline.status, started by the chief as a background Bash) is reported as such, not as missing; close reads the status once and never waits.
Exits 1 when any step fails. On success the slug's state folder, the gate and test logs of earlier runs and the close log are deleted;
on failure nothing is deleted, so the close can be rerun.
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from baseline import LOCKFILES
from kit_config import load, repo_root
from new_failures import NO_SUMMARY, failures, has_summary

GIT_TIMEOUT_SECONDS = 120
GATES_TIMEOUT_SECONDS = 1800
RUNNING_FRESH_SECONDS = 1800
CASES = ("C2", "C3", "C4", "C5", "C6")
HASH_ROOT_FILES = ("package.json", "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", "conftest.py", "tsconfig.json", ".env.test",
                   ".nvmrc", ".python-version", "vitest.config.ts", "vitest.config.mts", "vitest.config.js", "vitest.config.mjs",
                   "vitest.workspace.ts", "vitest.workspace.js", "jest.config.ts", "jest.config.js", "jest.config.cjs", "jest.config.mjs",
                   "jest.config.json")
CACHE_KEEP_SECONDS = 3 * 86400
MAX_LINES = 24
DETAIL_LINES = 10
RETRO_FINDINGS = 5
SEVERITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}
OWNER = ("owner: executor fix", "next: executor fix with the printed lines, then executor close")
USER_BASELINE = ("owner: user", "next: user chooses: record the baseline now (it hides this change's own failures) or stop")
USER_REWRITE = ("owner: user", "next: user chooses: rewrite the history to add the trailer, or accept the commit without it")
OFFENDER = re.compile(r"^([0-9a-f]{8}) ")
FINDING = re.compile(r"^\s+\S+ \[(\w+)\]")


def default_slug(root: Path) -> str:
    try:
        line = (root / ".ai-kit" / "runs" / "current").read_text(encoding="utf-8").splitlines()[0].strip()
        if line:
            return line
    except (OSError, IndexError):
        pass
    return "default"


def run_cmd(cmd: list[str], timeout: float = GIT_TIMEOUT_SECONDS, **kwargs: object) -> subprocess.CompletedProcess:
    """The one subprocess call of this script: every command has a timeout, and a timeout is a 124 result, never a hang."""
    try:
        return subprocess.run(cmd, timeout=timeout, check=False, **kwargs)  # noqa: S603
    except subprocess.TimeoutExpired:
        empty = "" if kwargs.get("text") or kwargs.get("encoding") else b""
        return subprocess.CompletedProcess(cmd, 124, empty, f"timed out after {timeout:g} s: {' '.join(map(str, cmd[:3]))}" if isinstance(empty, str) else empty)


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return run_cmd(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")  # noqa: S607


def gates(root: Path, *args: str) -> subprocess.CompletedProcess:
    bash = os.environ.get("GATES_BASH") or shutil.which("bash") or "bash"
    try:
        return run_cmd([bash, "scripts/gates.sh", *args], GATES_TIMEOUT_SECONDS, cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    except OSError as exc:
        return subprocess.CompletedProcess([bash], 127, "", f"cannot run bash: {exc}")


STAMP_SKIP = (".claude/prd-flow/state/", ".ai-kit/")


def git_bytes(root: Path, *args: str, data: bytes | None = None) -> bytes:
    return run_cmd(["git", "-C", str(root), *args], input=data, capture_output=True).stdout  # noqa: S607


def tree_stamp(root: Path) -> str:
    """HEAD plus a hash of the content of every tracked change and of every untracked file (the kit's own state folders excluded):
    gates.sh compare writes the same string after its full run."""
    head = git_bytes(root, "rev-parse", "HEAD").decode().strip()
    diff = git_bytes(root, "diff", "HEAD", "--binary", "--no-ext-diff", "--", ".", ":(exclude).claude/prd-flow/state", ":(exclude).ai-kit")
    untracked = sorted(name for name in git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z").decode(errors="replace").split("\0")
                       if name and not name.startswith(STAMP_SKIP))
    hashes = git_bytes(root, "hash-object", "--stdin-paths", data="".join(f"{name}\n" for name in untracked).encode()).decode().split()
    body = diff + "\0".join(f"{name} {digest}" for name, digest in zip(untracked, hashes, strict=False)).encode()
    return f"{head} {git_bytes(root, 'hash-object', '--stdin', data=body).decode().strip()}"


def content_hash(root: Path) -> str:
    """A hash of what a test run depends on: the git trees of the source and test folders, the lockfiles, the root manifests and test
    configuration files, tests.hash_paths (paths tests read, for example docs/), the command and test configuration, and the dirty diff
    and untracked files of those paths. A docs-only commit leaves it unchanged unless docs/ is in tests.hash_paths."""
    config = load(root)
    tests = config.get("tests", {})
    paths = [*config.get("source_dirs", []), *(tests.get("test_dirs") or ["tests", "test", "__tests__", "spec", "e2e"]), *LOCKFILES,
             *HASH_ROOT_FILES, *tests.get("hash_paths", [])]
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(json.dumps([config.get("commands"), tests], sort_keys=True).encode())
    for path in paths:
        digest.update(f"{path} {git_bytes(root, 'rev-parse', '--verify', '-q', f'HEAD:{path}').decode().strip()}\n".encode())
    digest.update(git_bytes(root, "diff", "HEAD", "--binary", "--no-ext-diff", "--", *paths))
    untracked = sorted(name for name in git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z", "--", *paths).decode(errors="replace").split("\0")
                       if name)
    hashes = git_bytes(root, "hash-object", "--stdin-paths", data="".join(f"{name}\n" for name in untracked).encode()).decode().split()
    digest.update("\0".join(f"{name} {h}" for name, h in zip(untracked, hashes, strict=False)).encode())
    return digest.hexdigest()


def compare_log(root: Path, slug: str) -> tuple[Path, str] | None:
    """The full-run log of this exact tree (the stamp) or of the same test content (state/_compare/<hash>), with a label."""
    folder = root / ".claude" / "prd-flow" / "state" / slug
    stamp, final = folder / "final.stamp", folder / "final.log"
    if stamp.is_file() and final.is_file() and (folder / "exit").is_file() and stamp.read_text(encoding="utf-8").strip() == tree_stamp(root):
        return final, stamp.read_text(encoding="utf-8").split()[0][:8]
    key = content_hash(root)
    cached = root / ".claude" / "prd-flow" / "state" / "_compare" / key / "final.log"
    return (cached, key[:12]) if cached.is_file() and (cached.parent / "exit").is_file() else None


def runner_exit(final: Path) -> int:
    """The runner exit code stored beside the log; an unreadable one is a failure, never a pass."""
    try:
        return int((final.parent / "exit").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 1


def rerun_covers(folder: Path, final: Path, config: dict, base: set[str]) -> bool:
    """A rerun of the failing ids (gates.sh rerun), newer than the full run, that exited 0 with a summary and no new failure."""
    rerun, code = folder / "rerun.log", folder / "rerun.exit"
    if not (rerun.is_file() and code.is_file() and rerun.stat().st_mtime >= final.stat().st_mtime):
        return False
    if code.read_text(encoding="utf-8").strip() != "0" or not has_summary(rerun, config):
        return False
    return not failures(rerun, re.compile(config["failure_regex"])) - base - set(config.get("flaky", []))


def compare_running(root: Path, slug: str) -> bool:
    status = root / ".claude" / "prd-flow" / "state" / slug / "compare.status"
    try:
        running = status.read_text(encoding="utf-8").startswith("running")
    except OSError:
        return False
    return running and time.time() - status.stat().st_mtime < RUNNING_FRESH_SECONDS


def reuse_full_run(root: Path, slug: str) -> subprocess.CompletedProcess | None:
    """The compare step: read the result of a full run of this tree or of the same test content, once; the suite never runs here.
    None when there is no such run."""
    folder = root / ".claude" / "prd-flow" / "state" / slug
    found = compare_log(root, slug)
    if found is None:
        return None
    final, sha = found
    config = load(root)["tests"]
    if not has_summary(final, config):
        return subprocess.CompletedProcess([], 1, f"compare FAILED: {NO_SUMMARY}, log {final.relative_to(root).as_posix()}\n", "")
    base = {ln.strip() for ln in (folder / "baseline-failures.txt").read_text(encoding="utf-8").splitlines() if ln.strip()}
    seen = failures(final, re.compile(config["failure_regex"]))
    new = sorted(seen - base - set(config.get("flaky", [])))
    code = runner_exit(final)
    if not new:
        if code != 0 and not seen:
            return subprocess.CompletedProcess([], 1, f"compare FAILED: runner exited {code} without a failure line: not a pass, log {final.relative_to(root).as_posix()}\n", "")
        return subprocess.CompletedProcess([], 0, f"compare ok: reused the full run of {sha}, no new failures\n", "")
    listing = "".join(f"NEW {f}\n" for f in new) + f"new failures: {len(new)} (baseline: {len(base)})\n"
    if not config.get("rerun_ids", False):
        return subprocess.CompletedProcess([], 1, listing, "")
    if rerun_covers(folder, final, config, base):
        return subprocess.CompletedProcess([], 0, f"compare ok: reran {len(new)} failing id(s) of the full run of {sha}, all passed\n", "")
    ids = " ".join(shlex.quote(f) for f in new)
    return subprocess.CompletedProcess([], 1, listing + f"close never runs tests: run scripts/gates.sh rerun {slug} {ids} as a background Bash, then rerun close\n", "")


def gate_supports(root: Path, flag: str) -> bool:
    script = root / ".claude" / "skills" / "prd-flow" / "scripts" / "gate.py"
    if not script.is_file():
        return False
    out = run_cmd([sys.executable, "-B", str(script), "--help"], 60, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return flag in out.stdout + out.stderr


def baseline_status(root: Path, slug: str) -> str:
    status = root / ".claude" / "prd-flow" / "state" / slug / "baseline.status"
    return status.read_text(encoding="utf-8") if status.is_file() else ""


def baseline_running(root: Path, slug: str) -> bool:
    return baseline_status(root, slug).startswith("running")


def baseline_ok(root: Path, slug: str) -> bool:
    """The failures file counts only with a status that says the run finished: ok, or the watchdog's partial record."""
    file = root / ".claude" / "prd-flow" / "state" / slug / "baseline-failures.txt"
    return file.is_file() and baseline_status(root, slug).startswith(("ok", "watchdog"))


def valid_slug(slug: str) -> bool:
    return bool(slug) and ".." not in slug and "/" not in slug and "\\" not in slug


def clean_success(root: Path, slug: str, started: float, log: Path) -> None:
    state = root / ".claude" / "prd-flow" / "state"
    shutil.rmtree(state / slug, ignore_errors=True)
    shutil.rmtree(state / "_gate", ignore_errors=True)
    for cached in (state / "_compare").glob("*") if (state / "_compare").is_dir() else []:
        if cached.stat().st_mtime < started - CACHE_KEEP_SECONDS:
            shutil.rmtree(cached, ignore_errors=True)
    for item in (state / "_tests").glob("*") if (state / "_tests").is_dir() else []:
        if item.is_file() and item.stat().st_mtime < started:
            item.unlink(missing_ok=True)
    log.unlink(missing_ok=True)


def already_closed(root: Path, slug: str) -> bool:
    if (root / ".claude" / "prd-flow" / "state" / slug).exists():
        return False
    archive = root / "changes" / "archive"
    pattern = re.compile(rf"^\d+-{re.escape(slug)}$")
    if not (archive.is_dir() and any(d.is_dir() and pattern.match(d.name) for d in archive.iterdir())):
        return False
    log = run_git(root, "log", "--format=%s", "--fixed-strings", f"--grep=docs(prd): promote {slug}").stdout
    return any(ln.strip() == f"docs(prd): promote {slug}" for ln in log.splitlines())


def dirty_tracked(root: Path) -> list[str]:
    out = run_git(root, "status", "--short", "--untracked-files=no").stdout
    return [ln for ln in out.splitlines() if ln.strip()]


def split_dirty(lines: list[str]) -> tuple[list[str], list[str]]:
    promoted = [ln for ln in lines if ln[3:].strip('"').startswith(("docs/", "changes/"))]
    return promoted, [ln for ln in lines if ln not in promoted]


def needs_rewrite(root: Path, result: subprocess.CompletedProcess) -> bool:
    head = run_git(root, "rev-parse", "HEAD").stdout.strip()[:8]
    shas = [m.group(1) for ln in result.stdout.splitlines() if (m := OFFENDER.match(ln))]
    return any(sha != head for sha in shas)


def summarize(name: str, result: subprocess.CompletedProcess, owner: tuple[str, str] = OWNER) -> list[str]:
    lines = [ln for ln in (result.stdout + result.stderr).splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    if result.returncode == 0:
        return [last if last.startswith(name) else f"{name} ok" + (f": {last}" if last else "")]
    return [f"{name} FAILED (exit {result.returncode})", *owner] + [f"  {ln}" for ln in lines[-DETAIL_LINES:]]


def retro_block(result: subprocess.CompletedProcess) -> list[str]:
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    found = [(SEVERITY.get(m.group(1), 9), i, ln) for i, ln in enumerate(lines) if (m := FINDING.match(ln))]
    head = [ln for ln in lines if ln.startswith("retro")][:1] or summarize("retro", result)
    top = [ln for _, _, ln in sorted(found)[:RETRO_FINDINGS]]
    return head + top if found or head else summarize("retro", result)


def cleanup_lines(result: subprocess.CompletedProcess) -> list[str]:
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    if result.returncode == 0:
        return [f"cleanup ok ({lines[-1].strip()})" if lines else "cleanup ok"]
    return [f"cleanup left survivors (exit {result.returncode})", *(f"  {ln.strip()}" for ln in lines[-3:])]


def main() -> int:
    root = repo_root()
    if sys.argv[1:] == ["--stamp"]:
        print(tree_stamp(root))
        return 0
    if sys.argv[1:] == ["--hash"]:
        print(content_hash(root))
        return 0
    argv, case = sys.argv[1:], ""
    if "--case" in argv:
        at = argv.index("--case")
        case = argv[at + 1] if at + 1 < len(argv) else ""
        argv = argv[:at] + argv[at + 2:]
        if case not in CASES:
            print(f"close FAILED: --case must be one of {', '.join(CASES)}")
            return 2
    slug = argv[0] if argv else default_slug(root)
    if not valid_slug(slug):
        print(f"close FAILED: slug '{slug}' must not contain a path separator or '..'")
        return 2
    if already_closed(root, slug):
        print(f"close {slug}: already closed (state cleared, change archived)")
        return 0
    baseline = root / ".claude" / "prd-flow" / "state" / slug / "baseline-failures.txt"
    skip_suite = case == "C4"
    promoted, others = split_dirty(dirty_tracked(root))
    if promoted and (baseline_ok(root, slug) or skip_suite):
        print("\n".join([f"close {slug}", f"close FAILED: {len(promoted)} uncommitted tracked change(s)", "owner: executor fix",
                         "next: commit promote's output, then executor close", *[f"  {ln}" for ln in promoted[:5]]]))
        return 1
    started = time.time()
    log = root / ".claude" / "prd-flow" / "state" / "_close" / f"{slug}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"close {slug} started\n", encoding="utf-8")
    block, failed = [f"close {slug}"], False
    block += [f"note: modified tracked file left alone: {ln[3:].strip()}" for ln in others[:3]]
    final = ["docs", "--final", "--change", slug] if gate_supports(root, "--docs") else ["docs", "--final"]
    steps = [("lint", ["lint"]), ("trailers", ["trailers"]), ("gate --final", final), ("compare", ["compare", slug]), ("retro", ["retro"])]
    for name, args in steps:
        if name == "compare" and skip_suite:
            block.append(f"compare and baseline skipped (case {case}: no code change to prove)")
            continue
        if name == "compare" and not baseline_ok(root, slug):
            if baseline_running(root, slug):
                block += [f"compare FAILED: the baseline is still running in the background (state/{slug}/baseline.status)",
                          "owner: chief", "next: do not poll: the background baseline Bash raises a completion event; rerun close after it"]
            elif baseline.is_file():
                block.append(f"compare FAILED: baseline not recorded cleanly (status: {baseline_status(root, slug).strip() or 'none'}): "
                             f"rerun scripts/gates.sh baseline {slug}")
                block += USER_BASELINE
            else:
                block.append(f"compare FAILED: baseline missing: run scripts/gates.sh baseline {slug} before the first task")
                block += USER_BASELINE
            failed = True
            continue
        if name == "compare":
            result = reuse_full_run(root, slug)
            if result is None and compare_running(root, slug):
                block += [f"compare FAILED: the compare is still running in the background (state/{slug}/compare.status)",
                          "owner: chief", "next: do not poll: the background compare Bash raises a completion event; rerun close after it"]
                failed = True
                continue
            if result is None:
                block += ["compare FAILED: no compare result for this test content: close never runs the suite",
                          "owner: chief", f"next: run scripts/gates.sh compare {slug} as a background Bash, wait for its completion event, rerun close"]
                failed = True
                continue
        else:
            result = gates(root, *args)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(f"$ gates.sh {' '.join(args)}\n{result.stdout}{result.stderr}\n")
        owner = USER_REWRITE if name == "trailers" and result.returncode != 0 and needs_rewrite(root, result) else OWNER
        block += retro_block(result) if name == "retro" and result.returncode == 0 else summarize(name, result, owner)
        failed = failed or (result.returncode != 0 and name != "retro")
    block += cleanup_lines(gates(root, "cleanup", slug))
    status = run_git(root, "status", "--short").stdout
    block.append(f"tree: {len([ln for ln in status.splitlines() if ln.strip()])} changed path(s)")
    if failed:
        block.append(f"close FAILED, log {log.relative_to(root).as_posix()}")
    else:
        clean_success(root, slug, started, log)
        block.append("close ok, state and logs cleared")
    while len(block) > MAX_LINES:
        detail = [i for i, ln in enumerate(block[1:-1], 1) if ln.startswith("  ")]
        if not detail:
            block = block[: MAX_LINES - 1] + block[-1:]
            break
        del block[detail[-1]]
    print("\n".join(block))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

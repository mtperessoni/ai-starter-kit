"""Closing ceremony in one call: the full suite against the baseline, lint, trailers, the final gate, retro.

Usage: python scripts/close_gate.py [slug]     (through scripts/gates.sh close [slug])
Prints one block of at most 24 lines, every failure with `owner:` and `next:` lines (a missing baseline or a trailer that needs a history rewrite is `owner: user`) (the retro findings, at most 5, highest severity first; a failing check's last lines, at most 10); the full output of every step goes to .claude/prd-flow/state/_close/<slug>.log.
Refuses uncommitted tracked changes under docs/ and changes/ (promote's output, exit 1, after the baseline check); any other modified tracked file is a note line only.
Prints "already closed" (exit 0) only when the state is gone, changes/archive/<NNN>-<slug> exists and git log has "docs(prd): promote <slug>".
The compare step reuses a fresh full run (state/<slug>/final.stamp, written after the run, equals HEAD plus the content of every tracked change and untracked file): nothing runs, or only its new failing ids (gates.sh rerun) when tests.rerun_ids is true, whose failure_regex then yields ids the runner accepts; otherwise the full suite runs once.
A baseline still running (baseline.status, started by the chief as a background Bash) is reported as such, not as missing; close reads the status once and never waits.
Exits 1 when any step fails. On success the slug's state folder, the gate and test logs of earlier runs and the close log are deleted;
on failure nothing is deleted, so the close can be rerun.
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from kit_config import load, repo_root
from new_failures import failures

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


def gates(root: Path, *args: str) -> subprocess.CompletedProcess:
    bash = os.environ.get("GATES_BASH") or shutil.which("bash") or "bash"
    try:
        return subprocess.run([bash, "scripts/gates.sh", *args], cwd=root, capture_output=True, text=True,  # noqa: S603
                              encoding="utf-8", errors="replace", check=False)
    except OSError as exc:
        return subprocess.CompletedProcess([bash], 127, "", f"cannot run bash: {exc}")


STAMP_SKIP = (".claude/prd-flow/state/", ".ai-kit/")


def git_bytes(root: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], input=data, capture_output=True, check=False).stdout  # noqa: S603, S607


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


def reuse_full_run(root: Path, slug: str) -> subprocess.CompletedProcess | None:
    """The compare step when a fresh full run of this exact tree exists (W1.4): nothing to run, or only its new failing ids."""
    folder = root / ".claude" / "prd-flow" / "state" / slug
    stamp, final = folder / "final.stamp", folder / "final.log"
    if not (stamp.is_file() and final.is_file() and stamp.read_text(encoding="utf-8").strip() == tree_stamp(root)):
        return None
    config = load(root)["tests"]
    base = {ln.strip() for ln in (folder / "baseline-failures.txt").read_text(encoding="utf-8").splitlines() if ln.strip()}
    seen = failures(final, re.compile(config["failure_regex"]))
    new = sorted(seen - base - set(config.get("flaky", [])))
    sha = stamp.read_text(encoding="utf-8").split()[0][:8]
    if not new:
        return subprocess.CompletedProcess([], 0, f"compare ok: reused the full run of {sha}, no new failures\n", "")
    if not config.get("rerun_ids", False):
        return None
    rerun = gates(root, "rerun", slug, *new)
    if rerun.returncode == 0:
        return subprocess.CompletedProcess([], 0, f"compare ok: reran {len(new)} failing id(s) of the full run of {sha}, all passed\n", rerun.stderr)
    return rerun


def gate_supports(root: Path, flag: str) -> bool:
    script = root / ".claude" / "skills" / "prd-flow" / "scripts" / "gate.py"
    if not script.is_file():
        return False
    out = subprocess.run([sys.executable, "-B", str(script), "--help"], cwd=root, capture_output=True, text=True, encoding="utf-8",  # noqa: S603
                         errors="replace", check=False)
    return flag in out.stdout + out.stderr


def baseline_running(root: Path, slug: str) -> bool:
    status = root / ".claude" / "prd-flow" / "state" / slug / "baseline.status"
    return status.is_file() and status.read_text(encoding="utf-8").startswith("running")


def valid_slug(slug: str) -> bool:
    return bool(slug) and ".." not in slug and "/" not in slug and "\\" not in slug


def clean_success(root: Path, slug: str, started: float, log: Path) -> None:
    state = root / ".claude" / "prd-flow" / "state"
    shutil.rmtree(state / slug, ignore_errors=True)
    shutil.rmtree(state / "_gate", ignore_errors=True)
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
    log = subprocess.run(["git", "-C", str(root), "log", "--format=%s", "--fixed-strings", f"--grep=docs(prd): promote {slug}"],  # noqa: S603, S607
                         capture_output=True, text=True, encoding="utf-8", check=False).stdout
    return any(ln.strip() == f"docs(prd): promote {slug}" for ln in log.splitlines())


def dirty_tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "status", "--short", "--untracked-files=no"], capture_output=True, text=True,  # noqa: S603, S607
                         encoding="utf-8", check=False).stdout
    return [ln for ln in out.splitlines() if ln.strip()]


def split_dirty(lines: list[str]) -> tuple[list[str], list[str]]:
    promoted = [ln for ln in lines if ln[3:].strip('"').startswith(("docs/", "changes/"))]
    return promoted, [ln for ln in lines if ln not in promoted]


def needs_rewrite(root: Path, result: subprocess.CompletedProcess) -> bool:
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,  # noqa: S603, S607
                          encoding="utf-8", check=False).stdout.strip()[:8]
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


def main() -> int:
    root = repo_root()
    if sys.argv[1:] == ["--stamp"]:
        print(tree_stamp(root))
        return 0
    slug = sys.argv[1] if len(sys.argv) > 1 else default_slug(root)
    if not valid_slug(slug):
        print(f"close FAILED: slug '{slug}' must not contain a path separator or '..'")
        return 2
    if already_closed(root, slug):
        print(f"close {slug}: already closed (state cleared, change archived)")
        return 0
    baseline = root / ".claude" / "prd-flow" / "state" / slug / "baseline-failures.txt"
    promoted, others = split_dirty(dirty_tracked(root))
    if promoted and baseline.is_file():
        print("\n".join([f"close {slug}", f"close FAILED: {len(promoted)} uncommitted tracked change(s)", "owner: executor fix",
                         "next: commit promote's output, then executor close", *[f"  {ln}" for ln in promoted[:5]]]))
        return 1
    started = time.time()
    log = root / ".claude" / "prd-flow" / "state" / "_close" / f"{slug}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    block, failed, chunks = [f"close {slug}"], False, []
    block += [f"note: modified tracked file left alone: {ln[3:].strip()}" for ln in others[:3]]
    final = ["docs", "--final", "--change", slug] if gate_supports(root, "--docs") else ["docs", "--final"]
    steps = [("compare", ["compare", slug]), ("lint", ["lint"]), ("trailers", ["trailers"]),
             ("gate --final", final), ("retro", ["retro"])]
    for name, args in steps:
        if name == "compare" and not baseline.is_file():
            if baseline_running(root, slug):
                block += [f"compare FAILED: the baseline is still running in the background (state/{slug}/baseline.status)",
                          "owner: chief", "next: do not poll: the background baseline Bash raises a completion event; rerun close after it"]
            else:
                block.append(f"compare FAILED: baseline missing: run scripts/gates.sh baseline {slug} before the first task")
                block += USER_BASELINE
            failed = True
            continue
        result = reuse_full_run(root, slug) if name == "compare" else None
        result = result or gates(root, *args)
        chunks.append(f"$ gates.sh {' '.join(args)}\n{result.stdout}{result.stderr}")
        owner = USER_REWRITE if name == "trailers" and result.returncode != 0 and needs_rewrite(root, result) else OWNER
        block += retro_block(result) if name == "retro" and result.returncode == 0 else summarize(name, result, owner)
        failed = failed or (result.returncode != 0 and name != "retro")
    status = subprocess.run(["git", "-C", str(root), "status", "--short"], capture_output=True, text=True,  # noqa: S603, S607
                            encoding="utf-8", check=False).stdout
    block.append(f"tree: {len([ln for ln in status.splitlines() if ln.strip()])} changed path(s)")
    log.write_text("\n".join(chunks), encoding="utf-8")
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

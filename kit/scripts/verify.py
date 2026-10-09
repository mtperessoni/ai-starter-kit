"""One verification per wave or batch: the related tests of every file changed since a ref, the structure tests, the docs gate.

Usage: python scripts/verify.py <slug> [--since REF]     (through scripts/gates.sh verify <slug> [--since REF])
The ref defaults to the commit of the last verification (state/<slug>/verify.stamp), else the commit that added the change's plan.md, else the
merge base with the base branch. Steps: tests (gates.sh related <changed files>: the ratchet, the mirror and importer tests and tests.always)
and docs (gates.sh docs <slug>). The output goes to state/<slug>/verify.log; the screen gets at most 12 lines. A reminder, never a block on
other work: exit 1 only when a step failed.
When nothing changed since the last verification (the stamp holds HEAD plus a hash of the tree), only the steps that failed then rerun.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from close_gate import tree_stamp, valid_slug
from kit_config import load, repo_root

DETAIL_LINES = 6
STUCK_ALIVE_S, STUCK_IDLE_S, STUCK_FORGET_S = 1800, 600, 6 * 3600
TOOL_EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")
BASES = ("origin/main", "origin/staging", "origin/master", "main", "staging", "master")


def git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)  # noqa: S603, S607
    return out.stdout.strip() if out.returncode == 0 else ""


def default_ref(root: Path, slug: str, stamp: dict) -> str:
    if stamp.get("head"):
        return stamp["head"]
    for plan in sorted((root / "changes").glob(f"*-{slug}/plan.md")) if (root / "changes").is_dir() else []:
        commit = git(root, "log", "--diff-filter=A", "--format=%H", "--", plan.relative_to(root).as_posix()).splitlines()
        if commit:
            return commit[-1]
    for base in BASES:
        merged = git(root, "merge-base", "HEAD", base)
        if merged:
            return merged
    return "HEAD"


def changed_files(root: Path, ref: str) -> list[str]:
    tracked = git(root, "diff", "--name-only", "--diff-filter=d", ref).splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    skip = (".claude/prd-flow/state/", ".ai-kit/")
    return sorted({name for name in tracked + untracked if name and not name.startswith(skip)})


def gates(root: Path, *args: str) -> subprocess.CompletedProcess:
    bash = os.environ.get("GATES_BASH") or shutil.which("bash") or "bash"
    try:
        return subprocess.run([bash, "scripts/gates.sh", *args], cwd=root, capture_output=True, text=True,  # noqa: S603
                              encoding="utf-8", errors="replace", check=False)
    except OSError as exc:
        return subprocess.CompletedProcess([bash], 127, "", f"cannot run bash: {exc}")


def stuck_agents(root: Path) -> list[str]:
    """Agents of the run's events that have an agent_stuck event and no SubagentStop after it."""
    runs = root / ".ai-kit" / "runs"
    try:
        name = re.sub(r"[^\w.-]", "-", (runs / "current").read_text(encoding="utf-8").splitlines()[0].strip())
    except (OSError, IndexError):
        name = ""
    path = runs / name / "events.jsonl"
    if not path.is_file():
        found = sorted(runs.glob("*/events.jsonl"), key=lambda p: p.stat().st_mtime) if runs.is_dir() else []
        if not found:
            return []
        path = found[-1]
    stuck: dict[str, None] = {}
    live: dict[str, dict[str, float]] = {}
    try:
        with path.open("rb") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                agent = event.get("agent") if isinstance(event, dict) else None
                if not agent or agent == "main":
                    continue
                kind, ts = event.get("ev"), event.get("ts")
                if kind == "agent_stuck":
                    stuck[agent] = None
                elif kind == "SubagentStop":
                    stuck.pop(agent, None)
                    live.pop(agent, None)
                elif kind == "SubagentStart" and isinstance(ts, (int, float)):
                    live[agent] = {"start": ts, "last": ts}
                elif kind in TOOL_EVENTS and agent in live and isinstance(ts, (int, float)):
                    live[agent]["last"] = ts
    except OSError:
        return []
    now = time.time()
    for agent, seen in live.items():
        if now - seen["start"] > STUCK_FORGET_S:
            stuck.pop(agent, None)
        elif now - seen["last"] > STUCK_IDLE_S or now - seen["start"] > STUCK_ALIVE_S:
            stuck[agent] = None
    return list(stuck)


def preflight(root: Path, stuck: list[str]) -> tuple[list[str], str]:
    """Reap this session's stuck processes first, then name the stuck agents: (lines for the screen, text for the log)."""
    result = gates(root, "reap")
    text = (result.stdout + result.stderr).strip()
    lines = []
    if "reaped:" in text:
        reaped = re.search(r"reaped:\s*(\d+)", text)
        left = re.search(r"left:\s*(.*)", text)
        if (reaped and int(reaped.group(1))) or (left and left.group(1).strip() != "0"):
            lines.append(f"reap: reaped {reaped.group(1) if reaped else '?'}, left {left.group(1).strip() if left else '?'}")
    if stuck:
        lines.append("stuck agents: " + ", ".join(stuck))
    return lines, "$ gates.sh reap\n" + text


def failure_details(lines: list[str], pattern: re.Pattern) -> list[str]:
    """The failed test ids with the first assertion line of each, never the slowest tests. A short-summary line
    ("FAILED id - AssertionError: x") carries its own message; otherwise the first "E " or assertion line after the id."""
    details = []
    for index, line in enumerate(lines):
        match = pattern.search(line)
        if not match:
            continue
        ident = match.group(1) if match.groups() else line.strip()
        message = line.split(" - ", 1)[1].strip() if " - " in line else ""
        for later in lines[index + 1:index + 40] if not message else []:
            stripped = later.strip()
            if pattern.search(later):
                break
            if stripped.startswith("E ") or "AssertionError" in stripped or stripped.startswith("assert "):
                message = stripped
                break
        details.append(f"FAILED {ident}" + (f": {message}" if message else ""))
    return list(dict.fromkeys(details))


def read_stamp(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-") or not valid_slug(argv[0]):
        print("usage: gates.sh verify <slug> [--since REF]", file=sys.stderr)
        return 2
    slug, since = argv[0], None
    if "--since" in argv:
        index = argv.index("--since")
        since = argv[index + 1] if index + 1 < len(argv) else None
        if not since:
            print("verify: --since needs a ref", file=sys.stderr)
            return 2
    root = repo_root()
    folder = root / ".claude" / "prd-flow" / "state" / slug
    folder.mkdir(parents=True, exist_ok=True)
    stamp_path, log = folder / "verify.stamp", folder / "verify.log"
    failure_regex = re.compile(load(root).get("tests", {}).get("failure_regex") or r"^(?:FAILED|ERROR)\s+(\S+)")
    stuck = stuck_agents(root)
    stamp = read_stamp(stamp_path)
    tree = tree_stamp(root)
    unchanged = stamp.get("tree") == tree and since is None
    previous = list(stamp.get("failed", [])) if unchanged else None
    if unchanged and not previous and not stuck:
        print(f"verify {slug}: ok, nothing changed since the last verification")
        return 0
    notes, reap_text = preflight(root, stuck)
    if unchanged and not previous:
        print("\n".join([f"verify {slug}: ok, nothing changed since the last verification", *notes]))
        return 0
    ref = since or default_ref(root, slug, stamp)
    files = changed_files(root, ref)
    steps = [("tests", ["related", *files]) if files else ("tests", None), ("docs", ["docs", slug])]
    out, failed, chunks = [f"verify {slug}: {len(files)} changed file(s) since {ref[:8]}", *notes], [], [reap_text]
    for name, args in steps:
        if previous is not None and name not in previous:
            out.append(f"{name} ok (unchanged since the last verification)")
            continue
        if args is None:
            out.append("tests skipped: no changed files")
            continue
        result = gates(root, *args)
        text = (result.stdout + result.stderr).splitlines()
        chunks.append(f"$ gates.sh {' '.join(args[:2])}{' ...' if len(args) > 2 else ''}\n" + "\n".join(text))
        lines = [ln for ln in text if ln.strip()]
        if result.returncode == 0:
            out.append(f"{name} ok" + (f": {lines[-1]}" if lines else ""))
        else:
            failed.append(name)
            found = failure_details(lines, failure_regex)
            shown = found[:DETAIL_LINES] if found else lines[-DETAIL_LINES:]
            out += [f"{name} FAILED (exit {result.returncode})", *[f"  {ln}" for ln in shown]]
    log.write_text("\n".join(chunks), encoding="utf-8")
    stamp_path.write_text(json.dumps({"head": git(root, "rev-parse", "HEAD"), "tree": tree_stamp(root), "failed": failed, "ts": int(time.time())}), encoding="utf-8")
    out.append(f"verify {'FAILED' if failed else 'ok'}, log {log.relative_to(root).as_posix()}")
    print("\n".join(out[:11] + out[-1:] if len(out) > 12 else out))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

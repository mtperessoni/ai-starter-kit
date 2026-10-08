"""Closing ceremony in one call: the full suite against the baseline, lint, trailers, the final gate, retro.

Usage: python scripts/close_gate.py [slug]     (through scripts/gates.sh close [slug])
Prints one block of at most 15 lines; the full output of every step goes to .claude/prd-flow/state/_close/<slug>.log.
Exits 1 when any step fails.
"""

import os
import subprocess
import sys
from pathlib import Path

from kit_config import repo_root

MAX_LINES = 15
DETAIL_LINES = 2


def default_slug(root: Path) -> str:
    try:
        line = (root / ".ai-kit" / "runs" / "current").read_text(encoding="utf-8").splitlines()[0].strip()
        if line:
            return line
    except (OSError, IndexError):
        pass
    return "default"


def gates(root: Path, *args: str) -> subprocess.CompletedProcess:
    bash = os.environ.get("GATES_BASH") or "bash"
    return subprocess.run([bash, "scripts/gates.sh", *args], cwd=root, capture_output=True, text=True,  # noqa: S603
                          encoding="utf-8", errors="replace", check=False)


def summarize(name: str, result: subprocess.CompletedProcess) -> list[str]:
    lines = [ln for ln in (result.stdout + result.stderr).splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    ok = result.returncode == 0
    status = "ok" if ok else f"FAILED (exit {result.returncode})"
    head = last if last.startswith(name) and ok else f"{name} {status}" + (f": {last}" if last else "")
    if ok:
        return [head]
    return [head] + [f"  {ln}" for ln in lines[-1 - DETAIL_LINES:-1]]


def main() -> int:
    root = repo_root()
    slug = sys.argv[1] if len(sys.argv) > 1 else default_slug(root)
    log = root / ".claude" / "prd-flow" / "state" / "_close" / f"{slug}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    baseline = root / ".claude" / "prd-flow" / "state" / slug / "baseline-failures.txt"
    block, failed, chunks = [f"close {slug}"], False, []
    steps = [("compare", ["compare", slug]), ("lint", ["lint"]), ("trailers", ["trailers"]),
             ("gate --final", ["docs", "--final"]), ("retro", ["retro"])]
    for name, args in steps:
        if name == "compare" and not baseline.is_file():
            block.append(f"compare FAILED: no baseline for {slug}, run scripts/gates.sh baseline {slug} first")
            failed = True
            continue
        result = gates(root, *args)
        chunks.append(f"$ gates.sh {' '.join(args)}\n{result.stdout}{result.stderr}")
        block += summarize(name, result)
        failed = failed or (result.returncode != 0 and name != "retro")
    status = subprocess.run(["git", "-C", str(root), "status", "--short"], capture_output=True, text=True,  # noqa: S603, S607
                            encoding="utf-8", check=False).stdout
    block.append(f"tree: {len([ln for ln in status.splitlines() if ln.strip()])} changed path(s)")
    log.write_text("\n".join(chunks), encoding="utf-8")
    block.append(f"close {'FAILED' if failed else 'ok'}, log {log.relative_to(root).as_posix()}")
    if len(block) > MAX_LINES:
        block = block[: MAX_LINES - 1] + block[-1:]
    print("\n".join(block))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

"""Hotspots (rule PC12): code files ranked by commits touching them in a window times their lines.

The readiness plan splits the top of this list first; a large file nobody changes waits.
Usage: python scripts/hotspots.py [--days 180] [--top 15]
"""

import argparse
import subprocess
import sys
from collections import Counter

from kit_config import code_files, is_generated, is_test, line_count, load, rel, repo_root


def shallow(root) -> bool:
    out = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],  # noqa: S607
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return out.strip() == "true"


def commits_per_file(root, days: int) -> Counter:
    out = subprocess.run(
        ["git", "-c", "core.quotepath=off", "log", f"--since={days}.days", "--name-only", "--format="],  # noqa: S607
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return Counter(line.strip() for line in out.splitlines() if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()
    root = repo_root()
    cfg = load(root)
    commits = commits_per_file(root, args.days)
    rows = []
    for p in code_files(root, cfg):
        r = rel(p, root)
        if is_generated(r, cfg) or not commits[r]:
            continue
        lines = line_count(p)
        limit = cfg["limits"]["test_lines" if is_test(r, cfg) else "module_lines"]
        rows.append((commits[r] * lines, r, commits[r], lines, lines > limit))
    print(f"hotspots: last {args.days} days, score = commits x lines")
    if shallow(root):
        print("hotspots: shallow clone, history is partial; run on a full clone")
    for score, r, n, lines, over in sorted(rows, reverse=True)[: args.top]:
        print(f"{r}  commits {n}  lines {lines}  score {score}{'  over limit' if over else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

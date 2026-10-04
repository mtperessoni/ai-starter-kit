"""New failures against a baseline (rule TS04).

Usage: python scripts/new_failures.py --extract <log> > <baseline-failures.txt>
       python scripts/new_failures.py <baseline-failures.txt> <log>
The second form prints the failures in <log> that are not in the baseline and exits 1 when there is any.
Failure lines are recognized by tests.failure_regex in ai-kit.json (group 1 is the test id).
"""

import re
import sys
from pathlib import Path

from kit_config import load, repo_root


def failures(log: Path, pattern: re.Pattern) -> set[str]:
    found = set()
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.search(line)
        if m:
            found.add(m.group(1) if m.groups() else line.strip())
    return found


def main() -> int:
    pattern = re.compile(load(repo_root())["tests"]["failure_regex"])
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--extract":
        for f in sorted(failures(Path(args[1]), pattern)):
            print(f)
        return 0
    if len(args) != 2:
        print(__doc__)
        return 2
    baseline_path, log = Path(args[0]), Path(args[1])
    baseline = {line.strip() for line in baseline_path.read_text(encoding="utf-8").splitlines() if line.strip()} if baseline_path.exists() else set()
    new = sorted(failures(log, pattern) - baseline)
    for f in new:
        print(f"NEW {f}")
    print(f"new failures: {len(new)} (baseline: {len(baseline)})")
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())

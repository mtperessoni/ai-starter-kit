"""New failures against a baseline; known flaky tests (tests.flaky, TS38) are listed, not counted.

Usage: python scripts/new_failures.py --extract <log> > <baseline-failures.txt>
       python scripts/new_failures.py [--exit-code N] <baseline-failures.txt> <log>
       python scripts/new_failures.py --require-summary <log>
The second form prints the failures in <log> that are not in the baseline and exits 1 when there is any; with --exit-code N it also
exits 1 when the runner exited N != 0 and the log holds no failure line at all. The third form exits 1 (and says so) when the runner
output has no summary line: the suite died before it finished.
Failure lines are recognized by tests.failure_regex in ai-kit.json (group 1 is the test id); an ERROR line and a timeout or killed
outcome also count. The summary line is tests.summary_regex (default below, covering pytest, vitest, jest, unittest, go, cargo).
"""

import re
import sys
from pathlib import Path

from kit_config import load, repo_root

NO_SUMMARY = "suite ended without its summary line"
DEFAULT_SUMMARY = (r"(?:\b\d+ (?:passed|failed|errors?|skipped|deselected|xfailed|xpassed|tests?)\b|\bno tests ran\b|^\s*Tests?:?\s+\d"
                   r"|Test Files\s+\d|^Ran \d+ tests?\b|\btest result:|^(?:ok|FAIL)\s+\S+\s+[\d.]+s)")
ERROR_LINE = re.compile(r"^ERROR\b[: ]*(\S.*)?$")
KILLED = re.compile(r"(\+{3,} Timeout|Timeout >\d|Test timed out|^Killed\b|^Terminated\b|Fatal Python error|\bos\._exit\b)")


def failures(log: Path, pattern: re.Pattern) -> set[str]:
    found = set()
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.search(line)
        if m:
            found.add(m.group(1) if m.groups() else line.strip())
        elif ERROR_LINE.match(line):
            found.add(line.strip())
        elif KILLED.search(line):
            found.add("killed: " + line.strip()[:80])
    return found


def has_summary(log: Path, tests: dict) -> bool:
    pattern = re.compile(tests.get("summary_regex") or DEFAULT_SUMMARY)
    return any(pattern.search(line) for line in log.read_text(encoding="utf-8", errors="replace").splitlines())


def main() -> int:
    tests = load(repo_root())["tests"]
    pattern = re.compile(tests["failure_regex"])
    flaky_ids = set(tests.get("flaky", []))
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--extract":
        for f in sorted(failures(Path(args[1]), pattern)):
            print(f)
        return 0
    if len(args) == 2 and args[0] == "--require-summary":
        if has_summary(Path(args[1]), tests):
            return 0
        print(NO_SUMMARY)
        return 1
    exit_code = 0
    if len(args) == 4 and args[0] == "--exit-code":
        exit_code, args = int(args[1]), args[2:]
    if len(args) != 2:
        print(__doc__)
        return 2
    baseline_path, log = Path(args[0]), Path(args[1])
    baseline = {line.strip() for line in baseline_path.read_text(encoding="utf-8").splitlines() if line.strip()} if baseline_path.exists() else set()
    seen = failures(log, pattern)
    found = seen - baseline
    for f in sorted(found & flaky_ids):
        print(f"FLAKY {f} (tests.flaky, TS38: not counted)")
    new = sorted(found - flaky_ids)
    for f in new:
        print(f"NEW {f}")
    print(f"new failures: {len(new)} (baseline: {len(baseline)})")
    if exit_code != 0 and not seen:
        print(f"runner exited {exit_code} without a failure line: not a pass, log {log.as_posix()}")
        return 1
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())

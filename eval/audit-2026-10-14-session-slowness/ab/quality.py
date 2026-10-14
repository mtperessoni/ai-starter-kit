"""Deterministic quality checks of one arm's worktree against the base commit.

Usage: python quality.py <worktree> <base> <python>
Q1 no stale 60 s window left in the PRD, the TRD or the window constant.
Q2 the window constant is 90 s.
Q3 a rule row mentions the countdown, and its ID is new or changed.
Q4 the changed or new test files pass (vitest, offline project).
Q5 the current docs gate (gate.py, default run) error count.
Q6 the proposed gate (gate_lite.py) error count.
Q7 commits, files and lines changed by kind.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def run(cmd, cwd, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, shell=isinstance(cmd, str))
    return p.returncode, p.stdout + p.stderr


def main() -> None:
    wt, base, py = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    out = []
    stale = []
    for f in list((wt / "docs/prd").rglob("*.md")) + list((wt / "docs/trd").rglob("*.md")):
        if f.name == "CHANGELOG.md":
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b60\s?s\b|\b60 seconds\b|60_000|60000", line) and re.search(r"window|janela|first drop|reconnect|reconex", line, re.I):
                stale.append(f"{f.relative_to(wt).as_posix()}:{n}")
    timing = next(wt.glob("src/app/triage/*/(internal)/components/conversational/lib/timing.ts"))
    m = re.search(r"RECONNECT_WINDOW_MS\s*=\s*([\d_]+)", timing.read_text(encoding="utf-8"))
    window = int(m.group(1).replace("_", "")) if m else None
    out.append(f"Q1 stale 60 s mentions in PRD/TRD: {len(stale)} {stale[:6]}")
    out.append(f"Q2 RECONNECT_WINDOW_MS = {window} ({'ok' if window == 90000 else 'WRONG'})")

    diff = run(["git", "diff", base, "--", "docs/prd"], wt)[1]
    new_rows = [l[1:] for l in diff.splitlines() if l.startswith("+|") and re.match(r"\+\|\s*[A-Z]{2,5}-\d{2,3}", l)]
    countdown = [r[:120] for r in new_rows if re.search(r"countdown|count down|seconds left|remaining|faltam|restam|segundos|\{s\}|\d+ s\b.*(left|remain)", r, re.I)]
    out.append(f"Q3 rule rows added or changed: {len(new_rows)}; mentioning the countdown: {len(countdown)}")

    tests = [p for p in run(["git", "diff", "--name-only", base], wt)[1].splitlines() if re.search(r"__tests__/.*\.test\.tsx?$", p)]
    if tests:
        code, log = run(["node", "./node_modules/vitest/vitest.mjs", "run", "--project", "unit", "--coverage.enabled=false", *tests], wt)
        summary = [l.strip() for l in log.splitlines() if re.search(r"Test Files|Tests ", l)]
        out.append(f"Q4 changed tests ({len(tests)} files): exit {code} {summary}")
    else:
        out.append("Q4 changed tests: NONE")

    code, log = run([py, "-B", ".claude/skills/prd-flow/scripts/gate.py", "--base", base], wt)
    errs = [l for l in log.splitlines() if l.startswith("ERROR") or re.match(r"\s*G\d+", l)]
    out.append(f"Q5 current gate.py: exit {code}, {len(errs)} error lines {[e[:90] for e in errs[:5]]}")
    code, log = run([py, "-I", str(HERE / "gate_lite.py"), "--repo", str(wt), "--base", base], wt)
    out.append(f"Q6 gate_lite: exit {code} {log.strip().splitlines()[-1] if log.strip() else ''}")

    commits = run(["git", "rev-list", "--count", f"{base}..HEAD"], wt)[1].strip()
    stat = run(["git", "diff", "--numstat", base], wt)[1]
    kinds = {}
    for l in stat.splitlines():
        a, d, p = l.split("\t")
        if a == "-":
            continue
        k = "docs" if re.search(r"^docs/|^changes/|CHANGELOG", p) else "test" if "__tests__" in p else "code"
        n, f = kinds.get(k, (0, 0))
        kinds[k] = (n + int(a) + int(d), f + 1)
    untracked = run(["git", "status", "--porcelain"], wt)[1].strip()
    out.append(f"Q7 commits {commits}; lines/files by kind {kinds}; uncommitted: {len(untracked.splitlines()) if untracked else 0}")
    print("\n".join(out))


if __name__ == "__main__":
    main()

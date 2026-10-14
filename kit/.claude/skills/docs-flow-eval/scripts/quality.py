"""Deterministic quality checks of one run's worktree, driven by a scenario file.

Usage: python quality.py <worktree> <scenario.json> <python>
Prints one line per check and a final JSON line (`RESULT {...}`) for results/history.

Q1 no stale old value left in docs/ (PRD, TRD, maps), outside the CHANGELOG and the allowed lines.
Q2 the scenario constant holds the expected value.
Q3 rule rows added or changed, and how many match the new-rule pattern.
Q4 the changed or new test files pass (vitest, offline project).
Q5 the change gate of the worktree's own (overlaid kit) prd-flow gate.py against the base: error lines.
Q6 retired with the eval's private gate.
Q7 commits, lines and files changed by kind.
Q8 the decision is recorded with its rejected alternative (commit bodies or changed files under changes/).
Q9 red evidence: a commit body or a delivery file names the failing run before the code.
Q10 test files added (a new hook or component test).
Q11 the INDEX IDs column is current (the worktree's gen_index.py --check).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run(cmd, cwd, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, ANSI.sub("", p.stdout + p.stderr)


def main() -> None:
    wt, sc, py = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")), sys.argv[3]
    base = sc["base"]
    r: dict = {}
    out = []

    stale_re = re.compile("|".join(sc["stale_patterns"]))
    ctx_re = re.compile(sc["stale_context"], re.I)
    allow_re = re.compile("|".join(sc.get("stale_allow", [])) or r"(?!)", re.I)
    stale = []
    for f in (wt / "docs").rglob("*.md"):
        if f.name == "CHANGELOG.md" or "archive" in f.parts:
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in stale_re.finditer(line):
                window = line[max(0, m.start() - 160): m.end() + 60]
                if ctx_re.search(window) and not allow_re.search(window):
                    stale.append(f"{f.relative_to(wt).as_posix()}:{n}")
                    break
    r["stale"] = len(stale)
    out.append(f"Q1 stale old value in docs/: {len(stale)} {stale[:6]}")

    c = sc["constant"]
    target = next(wt.glob(c["glob"]), None)
    m = re.search(c["regex"], target.read_text(encoding="utf-8")) if target else None
    value = int(m.group(1).replace("_", "")) if m else None
    r["constant_ok"] = value == c["expected"]
    out.append(f"Q2 constant = {value} ({'ok' if r['constant_ok'] else 'WRONG'})")

    diff = run(["git", "diff", base, "--", "docs/prd"], wt)[1]
    rows = [l[1:] for l in diff.splitlines() if re.match(r"\+\|\s*[A-Z]{2,5}-\d{2,3}\s*\|", l)]
    new_rule = [x for x in rows if re.search(sc["new_rule_pattern"], x, re.I)]
    r["rows_changed"], r["new_rule_rows"] = len(rows), len(new_rule)
    out.append(f"Q3 rule rows added or changed: {len(rows)}; matching the new rule: {len(new_rule)}")

    changed = run(["git", "diff", "--name-only", base], wt)[1].splitlines()
    tests = [p for p in changed if re.search(r"__tests__/.*\.test\.tsx?$", p)]
    if tests:
        code, log = run(["node", "./node_modules/vitest/vitest.mjs", "run", "--project", "unit", "--coverage.enabled=false", *tests], wt)
        summary = " ".join(l.strip() for l in log.splitlines() if re.search(r"Test Files|Tests ", l))
        r["tests_pass"] = code == 0
        out.append(f"Q4 changed tests ({len(tests)} files): exit {code} {summary}")
    else:
        r["tests_pass"] = False
        out.append("Q4 changed tests: NONE")

    code, log = run([py, "-B", ".claude/skills/prd-flow/scripts/gate.py", "--base", base], wt)
    errs = [l for l in log.splitlines() if l.startswith("ERROR")]
    r["gate_current_errors"] = len(errs)
    out.append(f"Q5 current gate.py: exit {code}, {len(errs)} errors {sorted({e.split()[1] for e in errs})}")

    commits = run(["git", "rev-list", "--count", f"{base}..HEAD"], wt)[1].strip()
    kinds: dict = {}
    for l in run(["git", "diff", "--numstat", base], wt)[1].splitlines():
        a, d, p = l.split("\t")
        if a == "-":
            continue
        k = "docs" if re.search(r"^docs/|^changes/|CHANGELOG", p) else "test" if "__tests__" in p else "code"
        n, f = kinds.get(k, (0, 0))
        kinds[k] = (n + int(a) + int(d), f + 1)
    r["commits"], r["churn"] = int(commits or 0), kinds
    out.append(f"Q7 commits {commits}; lines/files by kind {kinds}")

    bodies = run(["git", "log", "--format=%B", f"{base}..HEAD"], wt)[1]
    changed_docs = [wt / p for p in changed if p.startswith("changes/") and p.endswith(".md") and (wt / p).is_file()]
    record = bodies + "\n" + "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in changed_docs)
    decided = bool(re.search(sc["decision_regex"], record, re.I))
    rejected = bool(re.search(sc["rejected_regex"], record, re.I))
    r["decision_recorded"] = decided and rejected
    out.append(f"Q8 decision recorded: {decided}; rejected alternative recorded: {rejected}")

    deliveries = wt / ".claude/prd-flow/state" / sc["slug"] / "deliveries"
    red_text = bodies + ("\n".join(p.read_text(encoding="utf-8", errors="replace") for p in deliveries.glob("*.md")) if deliveries.is_dir() else "")
    r["red_evidence"] = bool(re.search(r"^\s*Red:\s*\S", red_text, re.M))
    out.append(f"Q9 red evidence in commit bodies or deliveries: {r['red_evidence']}")

    added = [p for p in run(["git", "diff", "--name-only", "--diff-filter=A", base], wt)[1].splitlines() if "__tests__/" in p]
    r["tests_added"] = len(added)
    out.append(f"Q10 test files added: {len(added)} {added[:3]}")

    code, log = run([py, "-I", ".claude/skills/prd-flow/scripts/gen_index.py", "--repo", str(wt), "--check"], wt)
    r["index_current"] = code == 0
    out.append(f"Q11 INDEX current: {code == 0} {log.strip()[:120]}")

    print("\n".join(out))
    print("RESULT " + json.dumps(r))


if __name__ == "__main__":
    main()

"""Proposed docs gate: five checks, one run, about a second.

L1 every rule ID is unique across the PRD.
L2 every rule row has its ID, rule text, source and change-via cells filled.
L3 every rule ID a test cites exists in the PRD.
L4 every rule row added or changed against --base is cited by at least one test.
L5 no em dash in files changed against --base.

Usage: python gate_lite.py --repo <path> --base <ref>
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROW = re.compile(r"^\|\s*([A-Z]{2,5}-\d{2,3})\s*\|(.*)\|\s*$")
TEST_GLOBS = ("src/**/__tests__/**/*.test.ts", "src/**/__tests__/**/*.test.tsx")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def rule_rows(text: str) -> dict[str, str]:
    rows = {}
    for line in text.splitlines():
        m = ROW.match(line.strip())
        if m:
            rows.setdefault(m.group(1), line.strip())
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    a = ap.parse_args()
    repo = Path(a.repo)
    errors: list[str] = []

    seen: dict[str, Path] = {}
    rows: dict[str, str] = {}
    for f in sorted((repo / "docs/prd").glob("*/*.md")):
        for line in f.read_text(encoding="utf-8").splitlines():
            m = ROW.match(line.strip())
            if not m:
                continue
            rid = m.group(1)
            if rid in seen and seen[rid] != f:
                errors.append(f"L1 {rid} is defined in {seen[rid].name} and {f.name}")
            seen[rid] = f
            rows[rid] = line.strip()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or not all(cells[:4]):
                errors.append(f"L2 {rid} has an empty ID, rule, source or change-via cell ({f.name})")

    prefixes = {rid.split("-")[0] for rid in rows}
    cite = re.compile(r"\b(" + "|".join(sorted(prefixes)) + r")-\d{2,3}\b") if prefixes else None
    cited: set[str] = set()
    for pattern in TEST_GLOBS:
        for f in repo.glob(pattern):
            for m in cite.finditer(f.read_text(encoding="utf-8", errors="replace")) if cite else []:
                rid = m.group(0)
                cited.add(rid)
                if rid not in rows:
                    errors.append(f"L3 {f.relative_to(repo).as_posix()} cites {rid}, which is not in the PRD")

    base_rows: dict[str, str] = {}
    for path in git(repo, "ls-tree", "-r", "--name-only", a.base, "docs/prd").splitlines():
        if path.endswith(".md") and path.count("/") == 3:
            base_rows.update(rule_rows(git(repo, "show", f"{a.base}:{path}")))
    for rid, line in rows.items():
        if base_rows.get(rid) != line and rid not in cited:
            errors.append(f"L4 {rid} was added or changed and no test cites it")

    for path in git(repo, "diff", "--name-only", a.base).splitlines() + git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
        p = repo / path
        if p.is_file() and chr(0x2014) in p.read_text(encoding="utf-8", errors="replace"):
            errors.append(f"L5 em dash in {path}")

    for e in sorted(set(errors)):
        print(e)
    print(f"gate-lite: {len(set(errors))} errors, {len(rows)} rules, {len(cited)} cited by tests")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

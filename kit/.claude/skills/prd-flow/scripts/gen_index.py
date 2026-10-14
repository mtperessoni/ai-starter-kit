"""Rewrite the IDs column of docs/prd/INDEX.md from the rule rows of each section file.

Usage: python gen_index.py --repo <path> [--prd docs/prd] [--check]
--check prints the rows whose IDs differ from the rule rows and exits 1 when any do; without it the file is rewritten.
A cell counts as current when it expands to the same ID set as the rule rows, whatever its format (the gate compares the same way).
IDs follow the gate: multi-segment prefixes (ABC-DEF-01) and a trailing letter (CNX-10a) are listed by themselves.
A row keeps its cell when its file has no rule rows (glossary, scope, open questions).
"""
import argparse
import re
import sys
from pathlib import Path

from gate_core import ID, expand

LINK = re.compile(r"^\|\s*\[[^\]]+\]\(([^)]+\.md)\)\s*\|")
RULE = re.compile(r"^\|\s*(" + ID + r")(?:\s*·\s*\w+)?\s*\|")
PARTS = re.compile(r"^(.*)-(\d+)([a-z]?)$")


def compress(ids: list[str]) -> str:
    by_prefix: dict[str, list[tuple[int, int]]] = {}
    suffixed: dict[str, list[str]] = {}
    for rid in ids:
        prefix, num, suffix = PARTS.match(rid).groups()
        if suffix:
            suffixed.setdefault(prefix, []).append(rid)
        else:
            by_prefix.setdefault(prefix, []).append((int(num), len(num)))
        by_prefix.setdefault(prefix, [])
    parts = []
    fmt = lambda x: str(x[0]).zfill(x[1])
    for prefix, nums in by_prefix.items():
        nums = sorted(set(nums))
        run = [nums[0]] if nums else []
        for n in nums[1:] + [(None, 0)]:
            if not run:
                break
            if n[0] is not None and n[0] == run[-1][0] + 1:
                run.append(n)
                continue
            if len(run) >= 3:
                parts.append(f"{prefix}-{fmt(run[0])}..{fmt(run[-1])}")
            else:
                parts.extend(f"{prefix}-{fmt(x)}" for x in run)
            run = [n]
        parts.extend(sorted(set(suffixed.get(prefix, []))))
    return ", ".join(parts)


def section_ids(section: Path) -> list[str]:
    return [r.group(1) for r in map(RULE.match, section.read_text(encoding="utf-8").splitlines()) if r]


def index_links(prd: Path) -> list[str]:
    return [m.group(1) for m in map(LINK.match, (prd / "INDEX.md").read_text(encoding="utf-8").splitlines()) if m]


def stale(prd: Path) -> tuple[list[str], list[tuple[str, str, str]]]:
    """The INDEX lines with the IDs column regenerated, and (section file, current cell, generated cell) per stale row."""
    lines = (prd / "INDEX.md").read_text(encoding="utf-8").splitlines()
    changed = []
    for i, line in enumerate(lines):
        m = LINK.match(line)
        if not m:
            continue
        section = prd / m.group(1)
        if not section.is_file():
            continue
        ids = section_ids(section)
        if not ids:
            continue
        cells = line.split("|")
        if len(cells) < 5:
            continue
        new = compress(ids)
        if expand(cells[3]) != set(ids):
            changed.append((m.group(1), cells[3].strip(), new))
            cells[3] = f" {new} "
            lines[i] = "|".join(cells)
    return lines, changed


def write(prd: Path) -> list[str]:
    lines, changed = stale(prd)
    if changed:
        (prd / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return [f"{rel}: {new}" for rel, _, new in changed]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--prd", default="docs/prd")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    prd = Path(a.repo) / a.prd
    changed = [f"{rel}: {new}" for rel, _, new in stale(prd)[1]] if a.check else write(prd)
    for c in changed:
        print(f"INDEX {'stale' if a.check else 'updated'}: {c}")
    return 1 if (changed and a.check) else 0


if __name__ == "__main__":
    sys.exit(main())

"""Rewrite the IDs column of docs/prd/INDEX.md from the rule rows of each section file.

Usage: python gen_index.py --repo <path> [--check]
--check prints the rows that would change and exits 1 when any would; without it the file is rewritten.
A row keeps its cell when its file has no rule rows (glossary, scope, open questions).
"""
import argparse
import re
import sys
from pathlib import Path

LINK = re.compile(r"^\|\s*\[[^\]]+\]\(([^)]+\.md)\)\s*\|")
RULE = re.compile(r"^\|\s*([A-Z]{2,5})-(\d{2,3})\s*\|")


def compress(ids: list[tuple[str, int, int]]) -> str:
    parts = []
    by_prefix: dict[str, list[tuple[int, int]]] = {}
    for prefix, num, width in ids:
        by_prefix.setdefault(prefix, []).append((num, width))
    for prefix, nums in by_prefix.items():
        nums = sorted(set(nums))
        run = [nums[0]]
        for n in nums[1:] + [(None, 0)]:
            if n[0] is not None and n[0] == run[-1][0] + 1:
                run.append(n)
                continue
            first, last = run[0], run[-1]
            fmt = lambda x: str(x[0]).zfill(x[1])
            if len(run) >= 3:
                parts.append(f"{prefix}-{fmt(first)}..{fmt(last)}")
            else:
                parts.extend(f"{prefix}-{fmt(x)}" for x in run)
            run = [n]
    return ", ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    prd = Path(a.repo) / "docs/prd"
    index = prd / "INDEX.md"
    lines = index.read_text(encoding="utf-8").splitlines()
    changed = []
    for i, line in enumerate(lines):
        m = LINK.match(line)
        if not m:
            continue
        section = prd / m.group(1)
        if not section.is_file():
            continue
        ids = [(r.group(1), int(r.group(2)), len(r.group(2))) for r in map(RULE.match, section.read_text(encoding="utf-8").splitlines()) if r]
        if not ids:
            continue
        cells = line.split("|")
        if len(cells) < 5:
            continue
        new = compress(ids)
        if cells[3].strip() != new:
            cells[3] = f" {new} "
            lines[i] = "|".join(cells)
            changed.append(f"{m.group(1)}: {new}")
    for c in changed:
        print(f"INDEX {'stale' if a.check else 'updated'}: {c}")
    if changed and not a.check:
        index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if (changed and a.check) else 0


if __name__ == "__main__":
    sys.exit(main())

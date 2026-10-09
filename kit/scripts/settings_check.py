"""Report permission deny rules that block a file the prd-flow writes.

Usage: python scripts/settings_check.py [--root DIR]
Reads .claude/settings.json and .claude/settings.local.json. A deny of Read, Edit, Write or MultiEdit (bare or with a
path pattern) that matches a PRD, TRD, change or state file stops the flow in the middle of a run. Exit 1 with one line
per rule, 0 when none.
"""

import json
import re
import sys
from pathlib import Path

from kit_config import repo_root

TOOLS = ("Read", "Edit", "Write", "MultiEdit")
WRITTEN = (
    "docs/prd/section.md",
    "docs/prd/CHANGELOG.md",
    "docs/trd/area.md",
    "changes/001-slug/plan.md",
    ".claude/prd-flow/state/slug/state.md",
)
RULE = re.compile(r"^(\w+)(?:\((.*)\))?$")


def glob_regex(pattern: str) -> re.Pattern[str]:
    pattern = pattern.strip().replace("\\", "/")
    for prefix in ("//", "./", "/"):
        if pattern.startswith(prefix):
            pattern = pattern[len(prefix):]
            break
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(rf"^{out}(?:/.*)?$")


def blocked(rule: str) -> str | None:
    m = RULE.match(rule.strip())
    if not m or m.group(1) not in TOOLS:
        return None
    if m.group(2) in (None, "", "*", "**"):
        return WRITTEN[0]
    regex = glob_regex(m.group(2))
    return next((path for path in WRITTEN if regex.match(path)), None)


def check(root: Path) -> list[str]:
    lines: list[str] = []
    for name in ("settings.json", "settings.local.json"):
        path = root / ".claude" / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            lines.append(f".claude/{name}: unreadable ({error})")
            continue
        for rule in (data.get("permissions") or {}).get("deny") or []:
            hit = blocked(str(rule))
            if hit:
                lines.append(f".claude/{name}: deny {rule} blocks files the flow writes (for example {hit}); remove it or narrow it")
    return lines


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) == 2 and argv[0] == "--root" else repo_root()
    lines = check(root)
    for line in lines:
        print(line)
    if not lines:
        print("settings-check ok")
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Change folder check (G15, G22) and the rule rows a status line reads."""

import re
from pathlib import Path

from gate_core import ID, Rules, err, expand, rule_table_ids


def rule_rows(rules: Rules, vias: set[str]) -> dict[str, list[str]]:
    return {
        rid: row for rid, (_, row) in rules.items()
        if rid in rule_table_ids and len(row) >= 3 and row[2].strip("` ").lower() in vias
    }


def check_change(folder: Path, rules: Rules) -> None:
    if not folder.is_dir():
        err("G22", f"change folder {folder} does not exist")
        return
    brief_path = folder / "brief.md"
    if not brief_path.exists():
        return
    brief = brief_path.read_text(encoding="utf-8")
    ids = {i for i in re.findall(r"\b(" + ID + r")\b", brief) if not i.startswith("I-")} | expand(brief)
    for rid in sorted(ids - set(rules)):
        err("G15", f"brief.md cites {rid}, which does not exist in the PRD")

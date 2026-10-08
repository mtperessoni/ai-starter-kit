"""Q4: an approved-rules file applied literally to the PRD."""

import re
from pathlib import Path

from gate_core import ID, ROW, Rules, cells, ends_with_path, err, literal_rows, parse_supersedes, section


CELLS = ["Rule", "Source", "Change via", "Example"]
CONFLICT_ID = re.compile(r"^\|\s*(" + ID + r")\s*\|(.*)\|\s*$")
RESOLUTIONS = {"rewritten", "superseded", "compatible"}


def norm(cell: str) -> str:
    return " ".join(cell.split())


def check_applied(path: Path, rules: Rules, cfg: dict[str, str]) -> None:
    prd_prefix = cfg["prd_dir"].rstrip("/") + "/"
    for rel, line in literal_rows(path.read_text(encoding="utf-8")):
        m = ROW.match(line)
        if not m:
            continue
        rid, row = m.group(1), cells(m.group(2))
        owner = rules.get(rid)
        if not owner:
            err("Q4", f"{rid} is not in the PRD yet")
        elif not ends_with_path(owner[0], rel.removeprefix(prd_prefix)):
            err("Q4", f"{rid} is in {owner[0].name}, not in {rel}")
        else:
            have = owner[1]
            for i, cell in enumerate(row):
                other = have[i] if i < len(have) else ""
                if norm(cell) != norm(other):
                    name = CELLS[i] if i < len(CELLS) else f"cell {i + 2}"
                    err("Q4", f"{rid}: {name} differs, approved '{norm(cell)[:110]}' vs PRD '{norm(other)[:110]}'")
                    break


def check_conflicts(path: Path, rules: Rules) -> None:
    text = path.read_text(encoding="utf-8")
    table: dict[str, list[str]] = {}
    for line in section(text, "Conflicts").splitlines():
        m = CONFLICT_ID.match(line.strip())
        if m:
            table[m.group(1)] = cells(m.group(2))
    pack = path.parent / "pack.md"
    pack_ids: set[str] = set()
    if pack.exists():
        found = re.search(r"^Conflicts:[ \t]*(.*)$", pack.read_text(encoding="utf-8"), re.M)
        pack_ids = set(re.findall(ID, found.group(1))) if found else set()
    for rid in sorted(pack_ids - set(table)):
        err("Q5", f"{rid} is in the Conflicts of pack.md and has no row under '## Conflicts'")
    approved = {m.group(1) for _, line in literal_rows(text) if (m := ROW.match(line))}
    superseded = set(parse_supersedes(section(text, "Supersedes")))
    for rid, row in sorted(table.items()):
        kind, note = (row[0].strip("` ").lower() if row else ""), (row[1].strip() if len(row) > 1 else "")
        if kind not in RESOLUTIONS:
            err("Q5", f"{rid}: Resolution '{kind}' is not one of {sorted(RESOLUTIONS)}")
        elif kind == "rewritten" and rid not in approved:
            err("Q5", f"{rid} is rewritten and has no row under its file heading", "add the rewritten row with the new text and the marker")
        elif kind == "superseded" and rid not in superseded:
            err("Q5", f"{rid} is superseded and is not listed under '## Supersedes' as 'ID: old text'")
        elif kind == "superseded" and rid not in rules:
            err("Q5", f"{rid} is superseded and does not exist in the PRD", "use the ID of an existing rule")
        elif kind == "compatible" and not note:
            err("Q5", f"{rid} is compatible and its Note is empty", "state in Note why the two rules hold together")

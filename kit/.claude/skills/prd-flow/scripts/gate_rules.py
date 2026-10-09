"""The approved set of a change: Q2 to Q5.

New route (no approved-rules.md or rules.md in the state folder): the set is the slug's CHANGELOG entry (the heading
names `changes/NNN-<slug>`; `IDs:`, `Conflicts:` and `Supersedes:` lines), the rows come from the PRD files and the
decisions from `changes/NNN-<slug>/decisions.md`. Old route: an approved-rules file applied literally to the PRD (Q4).
"""

import re
from pathlib import Path

from gate_core import ID, ROW, Rules, cells, ends_with_path, err, literal_rows, parse_supersedes, section
from gate_interview import check_mechanisms
from state_record import read


CELLS = ["Rule", "Source", "Change via", "Example"]
CONFLICT_ID = re.compile(r"^\|\s*(" + ID + r")\s*\|(.*)\|\s*$")
RESOLUTIONS = {"rewritten", "superseded", "compatible"}
PROMOTED = "Promoted: sources set."
REPLY = re.compile(r"^\s*Reply\s*\d*\s*:", re.I)


def norm(cell: str) -> str:
    return " ".join(cell.split())


def check_applied(path: Path, rules: Rules, cfg: dict[str, str], text: str | None = None) -> None:
    prd_prefix = cfg["prd_dir"].rstrip("/") + "/"
    for rel, line in literal_rows(text if text is not None else path.read_text(encoding="utf-8")):
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


def check_conflicts(path: Path, rules: Rules, text: str | None = None) -> None:
    text = text if text is not None else path.read_text(encoding="utf-8")
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


def slug_pattern(slug: str) -> str:
    return rf"changes/(?:archive/)?(?:\d+-)?{re.escape(slug)}(?![\w-])"


def entry_pattern(slug: str) -> str:
    return rf"^## [^\n]*{slug_pattern(slug)}[^\n]*\n.*?(?=^## |\Z)"


def changelog_entry(root: Path, cfg: dict[str, str], slug: str) -> str | None:
    text = read(root / cfg["prd_dir"].rstrip("/") / "CHANGELOG.md")
    m = re.search(entry_pattern(slug), text or "", re.M | re.S)
    return m.group(0) if m else None


def ids_of(entry: str, label: str) -> list[str]:
    ids: list[str] = []
    for m in re.finditer(rf"(?:^|\b){label}:[ \t]*(.*)$", entry, re.M):
        ids += re.findall(r"\b(" + ID + r")\b", m.group(1))
    return list(dict.fromkeys(ids))


def entry_sets(entry: str) -> dict[str, list[str]]:
    held = re.search(r"^Held planned:[ \t]*(.*?)\.[ \t]*Reason:", entry, re.M)
    return {"ids": ids_of(entry, "IDs"), "conflicts": ids_of(entry, "Conflicts"), "supersedes": ids_of(entry, "Supersedes"),
            "held": re.findall(r"\b(" + ID + r")\b", held.group(1)) if held else []}


def entry_approver(entry: str) -> str:
    m = re.match(r"## [^\n]*\(([^,()\n]*),\s*([^,()\n]*),\s*changes/", entry)
    return m.group(2).strip() if m else "unknown"


def change_ids(root: Path, cfg: dict[str, str], slug: str) -> set[str]:
    entry = changelog_entry(root, cfg, slug)
    return set(entry_sets(entry)["ids"]) if entry else set()


def find_change_dir(root: Path, slug: str) -> Path | None:
    for base in (root / "changes", root / "changes" / "archive"):
        for d in sorted(base.iterdir()) if base.is_dir() else []:
            if d.is_dir() and d.name != "archive" and (d.name == slug or d.name.split("-", 1)[-1] == slug):
                return d
    return None


def decisions_without_replies(change: Path | None) -> tuple[str, str]:
    """The decisions.md text without its Reply lines, and the Reply lines alone."""
    text = read(change / "decisions.md") if change else None
    lines = (text or "").splitlines()
    return "\n".join(ln for ln in lines if not REPLY.match(ln)), "\n".join(ln for ln in lines if REPLY.match(ln))


def check_entry(root: Path, cfg: dict[str, str], rules: Rules, slug: str, state: Path) -> bool:
    """The new-route checks replacing Q2 to Q5. False when the slug has no CHANGELOG entry."""
    entry = changelog_entry(root, cfg, slug)
    if entry is None:
        err("Q2", f"no CHANGELOG entry for changes/NNN-{slug} in {cfg['prd_dir'].rstrip('/')}/CHANGELOG.md",
            "write the entry with the docs agent in apply mode (heading names changes/NNN-<slug>, IDs:, Conflicts:, Supersedes: lines)")
        return False
    sets = entry_sets(entry)
    promoted = PROMOTED in entry
    marker = cfg["pending_marker"]
    if not sets["ids"]:
        err("Q2", "the CHANGELOG entry has no 'IDs:' line", "list every approved row of the change on an 'IDs:' line")
    for rid in sets["ids"]:
        owner = rules.get(rid)
        if not owner:
            err("Q2", f"{rid} is in the IDs of the CHANGELOG entry and not in the PRD")
        elif promoted and rid not in sets["held"] and marker in owner[1][0]:
            err("Q4", f"{rid} still carries the pending marker after promote")
        elif not promoted and marker not in owner[1][0]:
            err("Q2", f"{rid} is in the IDs of the CHANGELOG entry and its PRD row has no pending marker '{marker}'",
                "write the row with the marker, or remove the ID from the entry")
    if not promoted:
        for rid in sets["supersedes"]:
            if rid not in rules:
                err("Q5", f"{rid} is superseded in the CHANGELOG entry and does not exist in the PRD", "use the ID of an existing rule")
    pack = read(state / "pack.md")
    if pack:
        found = re.search(r"^Conflicts:[ \t]*(.*)$", pack, re.M)
        listed = set(sets["ids"]) | set(sets["supersedes"]) | set(sets["conflicts"])
        for rid in sorted(set(re.findall(ID, found.group(1))) - listed if found else set()):
            err("Q5", f"{rid} is in the Conflicts of pack.md and not in the IDs, Supersedes or Conflicts of the CHANGELOG entry",
                "add the ID with its resolution to the entry")
    body, replies = decisions_without_replies(find_change_dir(root, slug))
    rows = "\n".join(" ".join(rules[rid][1]) for rid in sets["ids"] if rid in rules)
    check_mechanisms(state, f"{body}\n{rows}", replies)
    return True

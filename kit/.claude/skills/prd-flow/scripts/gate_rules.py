"""The CHANGELOG entry of a change (heading names `changes/NNN-<slug>`; `IDs:`, `Conflicts:`, `Supersedes:` lines), read by promote.py."""

import re
from pathlib import Path

from gate_core import ID
from state_record import read


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

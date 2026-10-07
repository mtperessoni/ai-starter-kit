"""gate.py --sibling: shared PRD folders identical to the sibling repository's (G28)."""

import re
from pathlib import Path

from gate_core import PIPE, SEPARATOR, err, warn


def shared_section(text: str) -> str:
    m = re.search(r"^## Shared PRDs[^\n]*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def shared_rows(repo_md: Path) -> list[tuple[str, str]]:
    if not repo_md.exists():
        return []
    rows = []
    for line in shared_section(repo_md.read_text(encoding="utf-8")).splitlines():
        if not line.startswith("|") or SEPARATOR.match(line):
            continue
        cells = [c.strip().strip("`").strip() for c in PIPE.split(line.strip().strip("|"))]
        if len(cells) >= 2 and "<" not in line and cells[0].lower() != "prd folder" and cells[0] and cells[1]:
            rows.append((cells[0], cells[1]))
    return rows


def snapshot(folder: Path) -> dict[str, str]:
    files = {}
    for f in sorted(folder.rglob("*")):
        if f.is_file() and ".git" not in f.relative_to(folder).parts:
            text = f.read_bytes().decode("utf-8", errors="replace")
            files[f.relative_to(folder).as_posix()] = re.sub(r"\r\n?", "\n", text)
    return files


def check_sibling(root: Path, repo_md: Path) -> None:
    for folder, sibling in shared_rows(repo_md):
        mine, theirs = root / folder, root / sibling
        if not theirs.is_dir():
            warn("G28", f"sibling path {sibling} for {folder} does not exist locally; not compared")
            continue
        if not mine.is_dir():
            err("G28", f"{folder} does not exist in this repository")
            continue
        a, b = snapshot(mine), snapshot(theirs)
        for rel in sorted(set(a) - set(b)):
            err("G28", f"{folder}/{rel} exists here and not in {sibling}")
        for rel in sorted(set(b) - set(a)):
            err("G28", f"{folder}/{rel} exists in {sibling} and not here")
        for rel in sorted(k for k in set(a) & set(b) if a[k] != b[k]):
            err("G28", f"{folder}/{rel} differs from {sibling}")

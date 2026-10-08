"""G31 (PRD section files over prd_section_budget_lines) and G7 (CHANGELOG lines added by this change)."""

import re
from pathlib import Path

from gate_core import git, warn
from gate_output import park

MARKERS = r"\*\(\s*(?:approved|proposed|superseded|pending)[^)]*\)\*"


def strip_markers(text: str, cfg: dict[str, str]) -> str:
    text = re.sub(MARKERS, " ", text, flags=re.I)
    for word in (cfg["pending_marker"], cfg["proposed_marker"]):
        text = re.sub(r"\*\(\s*" + re.escape(word) + r"\s*\)\*", " ", text)
    return text


def added_lines(root: Path, base: str, rel: str) -> str:
    diff = git(root, "diff", "-U0", base, "--", rel)
    added = [x[1:] for x in diff.splitlines() if x.startswith("+") and not x.startswith("+++")]
    if git(root, "ls-files", "--others", "--exclude-standard", "--", rel).strip() and (root / rel).exists():
        added += (root / rel).read_text(encoding="utf-8").splitlines()
    return "\n".join(added)


def check_sections(root: Path, cfg: dict[str, str], prd: Path, changed: set[str] | None) -> None:
    budget = int(cfg["prd_section_budget_lines"])
    for f in sorted(prd.glob(cfg["prd_glob"])):
        rel = f.relative_to(root).as_posix()
        size = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        if size <= budget:
            continue
        text = f"{rel} has {size} lines, over prd_section_budget_lines {budget}; split it into smaller section files"
        if changed is None or rel in changed:
            warn("G31", text)
        else:
            park([f"WARNING G31 {text}"], rel)

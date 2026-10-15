"""Checks the change gate runs on the diff: a cited rule ID exists (G8), pending markers and Planned sections added (D4)."""

import re
import sys
from pathlib import Path

from gate_core import ID, Rules, err, git, rule_table_ids, warn


def added_by_file(root: Path, base: str, *paths: str) -> dict[str, list[str]]:
    """The lines the diff against base adds under paths, per file; a new untracked file counts whole."""
    found: dict[str, list[str]] = {}
    current = ""
    for line in git(root, "-c", "core.quotepath=false", "diff", "-U0", base, "--", *paths).splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("+") and current:
            found.setdefault(current, []).append(line[1:])
    for rel in git(root, "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "--", *paths).splitlines():
        if (root / rel).is_file():
            found[rel] = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
    return found


def kit_tests(root: Path) -> list[Path]:
    if not (root / "ai-kit.json").exists():
        return []
    sys.path.insert(0, str(root / "scripts"))
    import kit_config

    return kit_config.test_files(root, kit_config.load(root))


def check_cited_ids(root: Path, base: str, rules: Rules, trd_rel: str, tests: list[Path], changed: set[str]) -> None:
    """A rule ID cited by a TRD line or a test line the diff adds must be defined by a PRD row; only prefixes the PRD uses count as rule IDs."""
    prefixes = {re.sub(r"-\d+[a-z]?$", "", rid) for rid in rules}
    rels = [rel for rel in (p.relative_to(root).as_posix() for p in tests) if rel in changed]
    added = added_by_file(root, base, trd_rel, *rels) if (rels or trd_rel) else {}
    for rel, lines in sorted(added.items()):
        if not (rel.startswith(trd_rel + "/") and rel.endswith(".md")) and rel not in rels:
            continue
        seen: set[str] = set()
        for rid in re.findall(r"\b(" + ID + r")\b", "\n".join(lines)):
            if rid in rules or rid in seen or rid.startswith("I-") or re.sub(r"-\d+[a-z]?$", "", rid) not in prefixes:
                continue
            seen.add(rid)
            err("G8", f"{rel} cites {rid}, which no PRD row defines", "cite an ID that exists in docs/prd, or add the rule first")


def warn_added_planned(root: Path, cfg: dict[str, str], base: str, old: dict, new: dict, trd_rel: str) -> None:
    marker = cfg["pending_marker"]
    for rid, row in sorted(new.items()):
        if rid in rule_table_ids and marker in row[0] and not (rid in old and marker in old[rid][0]):
            warn("D4", f"{rid} gets a '{marker}' marker in this change; land the rule with its code instead")
    heading = re.escape(cfg["planned_heading"])
    added = [x[1:] for x in git(root, "diff", "-U0", base, "--", trd_rel).splitlines() if x.startswith("+") and not x.startswith("+++")]
    for rel in git(root, "ls-files", "--others", "--exclude-standard", "--", trd_rel).splitlines():
        added += (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
    if re.search(rf"^## {heading}", "\n".join(added), re.M):
        warn("D4", f"this change adds a '## {cfg['planned_heading']}' TRD section; land the rule with its code instead")

"""Checks the change gate adds for rule-as-data: INDEX current (S3), a changed rule has a test (G12), pending markers and Planned sections added (D4)."""

import re
import sys
from pathlib import Path

from gate_budget import added_by_file
from gate_core import EM_DASH, ID, Rules, err, git, rule_table_ids, warn
from gate_plan import read_allowlist, rule_rows
from gen_index import index_links, stale


def check_index_current(prd: Path, rules: Rules) -> None:
    if not (prd / "INDEX.md").exists():
        err("G2", f"{prd / 'INDEX.md'} does not exist (run the C0 bootstrap)")
        return
    for rel, cell, generated in stale(prd)[1]:
        err("G2", f"INDEX IDs column of {rel} is '{cell}' and the rule rows say '{generated}'", "run gate.py --fix (gen_index.py)")
    links = index_links(prd)
    for rel in links:
        if not (prd / rel).is_file():
            err("G2", f"INDEX points to a missing file: {rel}", "remove the row or restore the file")
    indexed = {(prd / rel).resolve() for rel in links}
    for f in sorted({src for src, _ in rules.values()}):
        if f.resolve() not in indexed:
            err("G2", f"{f.relative_to(prd).as_posix()} has rule rows and no row in INDEX.md", "add the file to INDEX.md, then run gate.py --fix")


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


def check_em_dash_added(root: Path, base: str, prd_rel: str, trd_rel: str) -> None:
    for rel, lines in sorted(added_by_file(root, base, prd_rel, trd_rel).items()):
        if rel.endswith(".md") and any(EM_DASH in line for line in lines):
            err("G4", f"em dash added in {rel}")


def check_changed_rules_tested(root: Path, rules: Rules, cfg: dict[str, str], vias: set[str], changed_ids: set[str]) -> None:
    if not changed_ids or not (root / "ai-kit.json").exists():
        return
    sys.path.insert(0, str(root / "scripts"))
    import kit_config

    kit = kit_config.load(root)
    cited: set[str] = set()
    for f in kit_config.test_files(root, kit):
        cited |= set(re.findall(r"\b(" + ID + r")\b", f.read_text(encoding="utf-8", errors="replace")))
    allowed = set(read_allowlist(root, kit).get("untested_rules", []))
    for rid, row in sorted(rule_rows(rules, vias).items()):
        if rid not in changed_ids or row[1].strip("` ").lower() == cfg["planned_source"]:
            continue
        if rid not in cited and rid not in allowed:
            err("G12", f"{rid} changed and has no test citing it and is not in allowlist.untested_rules")


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

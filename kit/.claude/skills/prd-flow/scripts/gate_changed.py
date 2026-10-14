"""Checks the change gate adds for rule-as-data: INDEX current (S3), a changed rule has a test (G12), pending markers and Planned sections added (D4)."""

import re
import sys
from pathlib import Path

from gate_core import ID, Rules, err, expand, git, rule_table_ids, warn
from gate_plan import read_allowlist, rule_rows
from gen_index import stale


def check_index_current(prd: Path) -> None:
    if not (prd / "INDEX.md").exists():
        err("G2", f"{prd / 'INDEX.md'} does not exist (run the C0 bootstrap)")
        return
    for rel, cell, generated in stale(prd)[1]:
        if expand(cell) != expand(generated):
            err("G2", f"INDEX IDs column of {rel} is '{cell}' and the rule rows say '{generated}'", "run gate.py --fix (gen_index.py)")


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

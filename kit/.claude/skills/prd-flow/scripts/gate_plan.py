"""Plan, trace, change folder and final checks."""

import re
import sys
from pathlib import Path

from gate_core import ID, ROW, TASK, Rules, cells, err, expand, is_code_route, is_proposed, is_table_line, warn


def check_plan(path: Path, rules: Rules, cfg: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    size = len(text.encode("utf-8"))
    budget = int(cfg["plan_budget_kb"]) * 1000
    if size > budget:
        warn("P1", f"plan with {size // 1000} KB: a new amendment goes in a file of its own")
    if not re.search(r"^## Plan execution rules", text, re.M):
        warn("P6", "plan without '## Plan execution rules' (review ceiling)")
    found = TASK.split(text)
    if len(found) < 3:
        err("P1", "plan without '### TNN' tasks")
        return
    prefixes = {rid.rsplit("-", 1)[0] for rid in rules}
    for tid, block in zip(found[1::2], found[2::2], strict=True):
        if re.search(r"^### \S+ · Promote", "### " + tid + block, re.M):
            continue
        if not re.search(r"^Owns:", block, re.M):
            err("P2", f"{tid} without 'Owns:'")
        if not re.search(r"^(Lens|Reviewer):", block, re.M):
            warn("P3", f"{tid} without 'Lens:' (an extra reviewer, or none)")
        if not re.search(r"^Model:", block, re.M):
            warn("P4", f"{tid} without 'Model:'")
        for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", block))):
            if rid.rsplit("-", 1)[0] in prefixes and rid not in rules:
                err("P5", f"{tid} cites {rid}, which does not exist in the PRD")


def source_files(source: str) -> list[str]:
    found = []
    for part in re.split(r"[,;]", source):
        path = part.strip("` ").split("::")[0].strip()
        if re.fullmatch(r"[\w./-]+\.\w+", path) and ("/" in path or path.lower() == path):
            found.append(path)
    return found


def rule_rows(rules: Rules, vias: set[str]) -> dict[str, list[str]]:
    return {rid: row for rid, (_, row) in rules.items() if len(row) >= 3 and row[2].strip("` ").lower() in vias}


def check_trace(root: Path, rules: Rules, cfg: dict[str, str], vias: set[str]) -> None:
    config_path = root / "ai-kit.json"
    if not config_path.exists():
        err("G22", "ai-kit.json not found: --trace needs test_patterns")
        return
    sys.path.insert(0, str(root / "scripts"))
    import kit_config

    kit = kit_config.load(root)
    cited: set[str] = set()
    for f in kit_config.test_files(root, kit):
        cited |= set(re.findall(r"\b(" + ID + r")\b", f.read_text(encoding="utf-8", errors="replace")))
    allowed = set(kit.get("allowlist", {}).get("untested_rules", []))
    for rid, row in sorted(rule_rows(rules, vias).items()):
        if row[1].strip("` ").lower() == cfg["planned_source"]:
            continue
        for rel in source_files(row[1]):
            if not (root / rel).exists():
                err("G11", f"{rid}: Source names {rel}, which does not exist")
        if rid in cited:
            if rid in allowed:
                err("G14", f"{rid} is tested now: remove it from allowlist.untested_rules")
        elif rid in allowed:
            warn("G13", f"{rid} has no test (listed in allowlist.untested_rules)")
        else:
            err("G12", f"{rid} has no test citing it and is not in allowlist.untested_rules")


def slice_ids(brief: str) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    head: list[str] = []
    for line in brief.splitlines():
        if not is_table_line(line):
            head = [] if not line.startswith("|") else head
            continue
        row = cells(line.strip().strip("|"))
        low = [c.lower() for c in row]
        if "slice" in low and "priority" in low and "rule ids" in low:
            head = low
        elif head and len(row) == len(head):
            found.append((row[head.index("slice")], row[head.index("priority")], row[head.index("rule ids")]))
    return found


def contract_ids(plan: str) -> set[str]:
    ids: set[str] = set()
    found = TASK.split(plan)
    for block in found[2::2]:
        m = re.search(r"^Contract\b.*?(?=^[A-Z][A-Za-z ]*:|\Z)", block, re.S | re.M)
        if m:
            ids |= set(re.findall(r"\b(" + ID + r")\b", m.group(0))) | expand(m.group(0))
    return ids


def check_change(folder: Path, rules: Rules) -> None:
    if not folder.is_dir():
        err("G22", f"change folder {folder} does not exist")
        return
    brief_path, design, plan = folder / "brief.md", folder / "design.md", folder / "plan.md"
    if not brief_path.exists():
        if design.exists():
            warn("G18", f"{design.name} without a brief.md stating size L")
        return
    brief = brief_path.read_text(encoding="utf-8")
    ids = {i for i in re.findall(r"\b(" + ID + r")\b", brief) if not i.startswith("I-")} | expand(brief)
    for rid in sorted(ids - set(rules)):
        err("G15", f"brief.md cites {rid}, which does not exist in the PRD")
    for line in brief.splitlines():
        m = ROW.match(line.strip())
        if m and len(cells(m.group(2))) >= 3:
            err("G17", f"brief.md holds the rule row {m.group(1)}: behavior is written once, in the PRD")
    if plan.exists():
        covered = contract_ids(plan.read_text(encoding="utf-8"))
        for name, priority, spec in slice_ids(brief):
            if priority.strip("` *").upper() != "P1":
                continue
            for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", spec)) | expand(spec)):
                if rid not in covered:
                    err("G16", f"slice '{name}' (P1): {rid} is in no task Contract of plan.md")
    if design.exists() and not re.search(r"\bsize\b[:\s*`=-]*L\b", brief, re.I):
        warn("G18", "design.md exists and brief.md does not state size L")


def check_final(root: Path, rules: Rules, cfg: dict[str, str], trd: Path) -> None:
    for rid, (_, row) in sorted(rules.items()):
        if is_proposed(row[0], cfg):
            err("G30", f"{rid} is still {cfg['proposed_marker']}: confront it and approve it, or drop it")
        elif len(row) >= 2 and (row[1].strip("` ").lower() == cfg["planned_source"] or cfg["pending_marker"] in row[0]):
            via = row[2].strip("` ").lower() if len(row) >= 3 else "code"
            if is_code_route(via):
                err("G19", f"{rid} is still planned or pending code")
            else:
                warn("G19", f"{rid} is still planned; it changes via {via} and closes by that route")
    for f in sorted(trd.rglob("*.md")):
        if re.search(r"^## " + re.escape(cfg["planned_heading"]), f.read_text(encoding="utf-8"), re.M):
            err("G20", f"{f.name} still has a '## {cfg['planned_heading']}' section")
    changes = root / "changes"
    if changes.is_dir():
        for d in sorted(changes.iterdir()):
            if d.is_dir() and d.name != "archive":
                err("G21", f"changes/{d.name} is still open: promote it and archive it")


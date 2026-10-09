"""Plan, trace, change folder and final checks."""

import re
import sys
from pathlib import Path

from gate_core import (
    ID, ROW, TASK, Rules, cells, err, expand, git, is_code_route, is_proposed, is_table_line, rule_table_ids, warn,
)
from gate_scope import approved_scope, heading_of_change, is_change_folder, read_snapshot, slug_of, write_snapshot


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
        if not re.search(r"^Read:", block, re.M):
            err("P10", f"{tid} without 'Read:' (exact paths or path::symbol the executor opens)")
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
    return {
        rid: row for rid, (_, row) in rules.items()
        if rid in rule_table_ids and len(row) >= 3 and row[2].strip("` ").lower() in vias
    }


def tracked_files(root: Path) -> list[str]:
    return git(root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()


def source_exists(root: Path, rel: str, tracked: list[str]) -> bool:
    """A bare name or partial path counts when it matches the last whole path segments of a tracked file."""
    if (root / rel).exists():
        return True
    tail = "/" + rel.lstrip("./")
    return any(("/" + f).endswith(tail) for f in tracked)


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
    tracked = tracked_files(root)
    for rid, row in sorted(rule_rows(rules, vias).items()):
        if row[1].strip("` ").lower() == cfg["planned_source"]:
            continue
        for rel in source_files(row[1]):
            if not source_exists(root, rel, tracked):
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


def final_drift(root: Path, rules: Rules, cfg: dict[str, str], trd: Path) -> list[dict]:
    found: list[dict] = []
    for rid, (_, row) in sorted(rules.items()):
        if is_proposed(row[0], cfg) or len(row) < 2:
            continue
        if row[1].strip("` ").lower() == cfg["planned_source"] or cfg["pending_marker"] in row[0]:
            via = row[2].strip("` ").lower() if len(row) >= 3 else "code"
            found.append({"code": "G19", "key": f"G19:{rid}", "ids": {rid}, "heading": "", "code_route": is_code_route(via), "via": via})
    for f in sorted(trd.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"^## " + re.escape(cfg["planned_heading"]) + r".*?(?=^## |\Z)", text, re.S | re.M):
            heading = m.group(0).splitlines()[0]
            ids = set(re.findall(ID, m.group(0)))
            found.append({"code": "G20", "key": f"G20:{f.name}:{heading}", "ids": ids, "heading": heading, "name": f.name})
    changes = root / "changes"
    if changes.is_dir():
        for d in sorted(changes.iterdir()):
            if d.is_dir() and d.name != "archive":
                found.append({"code": "G21", "key": f"G21:{d.name}", "ids": set(), "heading": "", "name": d.name})
    return found


def snapshot_drift(root: Path, rules: Rules, cfg: dict[str, str], trd: Path, slug: str) -> Path:
    keys = {d["key"] for d in final_drift(root, rules, cfg, trd)}
    return write_snapshot(root, slug, keys)


def final_message(d: dict, cfg: dict[str, str]) -> str:
    if d["code"] == "G19":
        return f"{next(iter(d['ids']))} is still planned or pending code"
    if d["code"] == "G20":
        return f"{d['name']} still has a '## {cfg['planned_heading']}' section"
    return f"changes/{d['name']} is still open: promote it and archive it"


def check_final(root: Path, rules: Rules, cfg: dict[str, str], trd: Path, change: str | None = None) -> None:
    for rid, (_, row) in sorted(rules.items()):
        if is_proposed(row[0], cfg):
            err("G30", f"{rid} is still {cfg['proposed_marker']}: confront it and approve it, or drop it")
    slug = slug_of(change) if change else None
    mine = approved_scope(root, slug) if slug else set()
    older = read_snapshot(root, slug) if slug else set()
    for d in final_drift(root, rules, cfg, trd):
        message = final_message(d, cfg)
        if d["code"] == "G19" and not d["code_route"]:
            warn("G19", f"{next(iter(d['ids']))} is still planned; it changes via {d['via']} and closes by that route")
            continue
        if slug is None:
            err(d["code"], message)
            continue
        if d["code"] == "G19":
            ours = bool(d["ids"] & mine)
        elif d["code"] == "G20":
            ours = heading_of_change(d["heading"], slug) or bool(d["ids"] & mine and "(" not in d["heading"])
        else:
            ours = is_change_folder(d["name"], slug)
        if ours:
            err(d["code"], message)
        else:
            tag = "pre-existing, outside this change" if d["key"] in older else f"another change, not {slug}"
            warn(d["code"], f"{message} ({tag})")

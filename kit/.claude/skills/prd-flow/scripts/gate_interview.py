"""The decision sheet: S0 to S6 on sheet.md and sheet-2.md, the Q3 mechanism check of the new route, and (old route only) Q3 on answers.md."""

import re
from pathlib import Path

from gate_core import ID, cells, err, is_table_line, warn
from state_record import read

LABELS = "What changes in the rules, What does not change, Assumed, Decisions, How to answer, Today:, Why it matters:, Example:, (Recommended)"
KINDS = {"rewrites", "adds", "supersedes", "removes"}
COMPARISON = re.compile(r"(?i)\b(above|below|more than|at least|high|higher|low|lower|after|before)\b")
ITEM = re.compile(r"^\*\*\s*(\d+)\.\s*(.+?)\s*\*\*(.*)$")
OPTION = re.compile(r"^\s*-\s+([A-Z])\)\s+(.*)$")
INTERACTS = re.compile(r"^\s*Interacts with:\s*(.*)$")
ASSUMED = re.compile(r"^\s*-\s+(A\d+)\b")
MECHANISM = re.compile(r"(?i)\b(env var|environment variable|switch|flag|configuration key|config key|table|endpoint|column)\b")
MAX_ITEMS = 8


def labels(cfg: dict[str, str]) -> dict[str, str]:
    names = ["diff", "scope", "assumed", "decisions", "answer", "today", "why", "example", "recommended"]
    parts = [p.strip() for p in (cfg.get("sheet_labels") or LABELS).split(",")]
    parts += [p.strip() for p in LABELS.split(",")][len(parts):]
    return dict(zip(names, parts))


def heading_body(text: str, label: str) -> str | None:
    found = None
    for m in re.finditer(r"^## (.*)$", text, re.M):
        if m.group(1).strip().lower().startswith(label.lower()):
            rest = text[m.end():]
            found = re.split(r"^## ", rest, maxsplit=1, flags=re.M)[0]
            break
    return found


def decisions(body: str, lab: dict[str, str]) -> list[dict]:
    items: list[dict] = []
    for line in body.splitlines():
        m = ITEM.match(line.strip())
        if m:
            items.append({"n": m.group(1), "title": m.group(2), "head": m.group(3), "lines": [], "opts": [], "inter": []})
        elif items:
            o = OPTION.match(line)
            if o:
                items[-1]["opts"].append(o.group(2))
                continue
            i = INTERACTS.match(line)
            if i:
                items[-1]["inter"] += re.findall(r"\d+", i.group(1))
            else:
                items[-1]["lines"].append(line.strip())
    return items


def pack_ids(pack: Path) -> set[str]:
    text = read(pack)
    if text is None:
        return set()
    ids = set(re.findall(r"\b(" + ID + r")\b", "\n".join(ln for ln in text.splitlines() if ln.startswith("Conflicts:"))))
    rules = heading_body(text, "Rules") or ""
    ids |= {m.group(1) for ln in rules.splitlines() if (m := re.match(r"^\|\s*(" + ID + r")\b", ln))}
    return ids


def lint_decisions(name: str, body: str, lab: dict[str, str], cfg: dict[str, str]) -> list[dict]:
    items = decisions(body, lab)
    words = [w.strip().lower() for w in cfg.get("plain_words", "").split(",") if w.strip()]
    nums = {d["n"] for d in items}
    if len(items) > MAX_ITEMS:
        err("S3", f"{name}: {len(items)} decisions (at most {MAX_ITEMS}); the change is too big: split it")
    for d in items:
        tag = f"{name} decision {d['n']}"
        text = [ln for ln in d["lines"] if ln]
        for key in ("today", "why", "example"):
            if not any(ln.lower().startswith(lab[key].lower()) for ln in text):
                err("S1", f"{tag} has no '{lab[key]}' line")
        if len(d["opts"]) < 2:
            err("S1", f"{tag} has fewer than two options")
        recommended = sum(lab["recommended"].lower() in o.lower() for o in d["opts"])
        if recommended != 1:
            err("S1", f"{tag} has {recommended} options marked {lab['recommended']} (exactly one)")
        d["ids"] = set(re.findall(r"\b(" + ID + r")\b", d["head"]))
        if not d["ids"] and "mechanism" not in d["head"].lower():
            err("S1", f"{tag} names no rule ID and is not marked '· mechanism'")
        shown = " ".join([d["title"], *d["opts"]]).lower()
        for word in words:
            if re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", shown):
                warn("S4", f"{tag} uses the jargon word '{word}' in its title or options: say it in the product's plain words")
        context = " ".join([d["title"], *[ln for ln in text if ln.lower().startswith((lab["today"].lower(), lab["why"].lower()))]])
        if COMPARISON.search(context) and not any(re.search(r"\d|\"[^\"]+\"|`[^`]+`", o) for o in d["opts"]):
            warn("S5", f"{tag} compares values but no option names a number or a category")
        for other in d["inter"]:
            if other not in nums or other == d["n"]:
                err("S6", f"{tag} interacts with decision {other}, which does not exist in {name}")
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if a["ids"] & b["ids"] and overlap(a["title"], b["title"]):
                err("S3", f"{name} decisions {a['n']} and {b['n']} decide the same rule ({', '.join(sorted(a['ids'] & b['ids']))}) and scope")
    return items


def overlap(a: str, b: str) -> bool:
    wa, wb = {w for w in re.findall(r"\w+", a.lower()) if len(w) > 3}, {w for w in re.findall(r"\w+", b.lower()) if len(w) > 3}
    small = min(len(wa), len(wb))
    return bool(small) and len(wa & wb) / small >= 0.6


def check_diff(text: str, lab: dict[str, str], pack: Path | None) -> None:
    body = heading_body(text, lab["diff"])
    if body is None:
        err("S0", f"sheet without the section '## {lab['diff']}'")
        return
    table = [cells(ln.strip().strip("|")) for ln in body.splitlines() if is_table_line(ln.strip())]
    if not table or len(table[0]) != 4:
        err("S0", "the diff table needs 4 columns: Rule, Today, Becomes, Kind")
        return
    ids: set[str] = set()
    for row in table[1:]:
        if len(row) != 4:
            err("S0", f"diff row with {len(row)} columns: {row[0][:40]}")
            continue
        if row[3].strip("` ").lower() not in KINDS:
            err("S0", f"diff row {row[0]}: Kind '{row[3]}' is not one of {sorted(KINDS)}")
        ids |= set(re.findall(r"\b(" + ID + r")\b", row[0]))
    for rid in sorted((pack_ids(pack) if pack else set()) - ids):
        err("S2", f"{rid} is touched or conflicting in the pack and is not a row of the diff table")
    if not any(ln.strip().startswith("- ") for ln in (heading_body(text, lab["scope"]) or "").splitlines()):
        err("S0", f"the section '## {lab['scope']}' needs at least one '- ' line")
    assumed = [ln for ln in (heading_body(text, lab["assumed"]) or "").splitlines() if ASSUMED.match(ln)]
    if len(assumed) > MAX_ITEMS:
        err("S3", f"{len(assumed)} assumed lines (at most {MAX_ITEMS})")


def check_sheet(target: Path, cfg: dict[str, str]) -> None:
    lab = labels(cfg)
    sheet = target if target.is_file() else target / "sheet.md"
    text = read(sheet)
    if text is None:
        err("S0", f"{sheet} not found", "write sheet.md with the surveyor in full mode")
        return
    check_diff(text, lab, sheet.parent / "pack.md")
    body = heading_body(text, lab["decisions"])
    if body is None:
        err("S0", f"sheet without the section '## {lab['decisions']}'")
    else:
        lint_decisions("sheet.md", body, lab, cfg)
    second = read(sheet.parent / "sheet-2.md")
    if second is not None:
        lint_decisions("sheet-2.md", heading_body(second, lab["decisions"]) or second, lab, cfg)


def sheet_items(state: Path, lab: dict[str, str]) -> list[str]:
    items: list[str] = []
    for name in ("sheet.md", "sheet-2.md"):
        text = read(state / name)
        if text is None:
            continue
        body = heading_body(text, lab["decisions"]) or ""
        items += [d["n"] for d in decisions(body, lab)]
        if name == "sheet.md":
            items += [m.group(1) for ln in (heading_body(text, lab["assumed"]) or "").splitlines() if (m := ASSUMED.match(ln))]
            items.append("scope")
    return list(dict.fromkeys(items))


def check_mechanisms(state: Path, written: str, replies: str = "") -> None:
    """New route: a mechanism term in the written decisions or rows must come from sheet.md, sheet-2.md or a Reply line."""
    known = " ".join([read(state / n) or "" for n in ("sheet.md", "sheet-2.md")] + [replies]).lower()
    for term in sorted({m.group(1).lower() for m in MECHANISM.finditer(written)}):
        if term not in known:
            err("Q3", f"the mechanism '{term}' appears in decisions.md or in the rows of the CHANGELOG IDs and in neither the sheet nor a Reply line",
                "ask it in a sheet decision or remove it")


def check_answers(state: Path, cfg: dict[str, str]) -> None:
    """Old route only (a state folder with approved-rules.md or rules.md): every sheet item answered, no unasked mechanism."""
    lab = labels(cfg)
    items = sheet_items(state, lab)
    if not items:
        return
    answers = read(state / "answers.md")
    if answers is None:
        err("Q3", f"answers.md not found beside the sheet in {state.name}", "write answers.md with the docs agent in apply mode")
        return
    body = heading_body(answers, "Resolution") or ""
    answered = {cells(ln.strip().strip("|"))[0].lower() for ln in body.splitlines() if is_table_line(ln.strip())}
    for item in items:
        if item.lower() not in answered:
            err("Q3", f"item {item} of the sheet has no row in answers.md '## Resolution'", "add the row: | Item | Answer | From |")
    known = " ".join(read(state / n) or "" for n in ("sheet.md", "sheet-2.md", "answers.md")).lower()
    written = " ".join(read(state / n) or "" for n in ("rules.md", "decisions.md"))
    for term in sorted({m.group(1).lower() for m in MECHANISM.finditer(written)}):
        if term not in known:
            err("Q3", f"the mechanism '{term}' appears in rules.md or decisions.md and in neither the sheet nor the answers", "ask it in a sheet decision or remove it")

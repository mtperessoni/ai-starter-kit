"""PRD structure checks: INDEX, HTML, pack and approved-rules rows."""

import re
from pathlib import Path

from gate_core import (
    ID, PACK_SECTIONS, ROW, SEPARATOR, Rules, baseline, cells, drift, err, expand, git, is_table_line, joined,
    literal_rows, read_html_rules, section, tokens, warn,
)


def check_index(prd: Path, rules: Rules, new: set[str]) -> None:
    index = prd / "INDEX.md"
    if not index.exists():
        err("G2", f"{index} does not exist (run the C0 bootstrap)")
        return
    by_file: dict[str, set[str]] = {}
    for line in index.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|[^|]*\|([^|]*)\|", line)
        if m:
            by_file[m.group(1).strip()] = expand(m.group(2))
    for rel, ids in by_file.items():
        f = prd / rel
        if not f.exists():
            err("G2", f"INDEX points to a missing file: {rel}")
            continue
        own = {rid for rid, (src, _) in rules.items() if src.resolve() == f.resolve()}
        for rid in sorted(ids - own):
            if rid not in rules:
                drift("G2", f"listed in INDEX and missing from the file ({rel})", rid)
        prefixes = {re.sub(r"-\d+[a-z]?$", "", i) for i in ids}
        for rid in sorted(own - ids):
            if re.sub(r"-\d+[a-z]?$", "", rid) in prefixes or not ids:
                if rid in new:
                    err("G2", f"{rid} exists in {rel} and is missing from the INDEX IDs column")
                else:
                    drift("G2", "missing from the INDEX IDs column", rid)
    indexed = {(prd / rel).resolve() for rel in by_file}
    for f in sorted({src for src, _ in rules.values()}):
        if f.resolve() in indexed:
            continue
        rel = f.relative_to(prd).as_posix()
        ids = {rid for rid, (src, _) in rules.items() if src == f}
        if ids & new:
            err("G2", f"{rel} has new rules and no row in INDEX.md")
        else:
            drift("G2", f"file without a row in INDEX.md ({rel})", sorted(ids)[0])


def changed_rows(root: Path, base: str, prd_rel: str, pattern: str):
    spec = f":(glob){prd_rel}/{pattern}"
    diff = git(root, "diff", "-U0", base, "--", spec)
    old: dict[str, list[str]] = {}
    new: dict[str, list[str]] = {}
    plain: list[tuple[str, str]] = []
    current = ""
    header_at = -1
    for line in diff.splitlines():
        if line.startswith("+") and SEPARATOR.match(line[1:]) and header_at == len(plain) - 1 >= 0:
            plain.pop()
        header_at = -1
        if line.startswith("+++ "):
            current = line[6:]
            continue
        if line.startswith("---"):
            continue
        m = ROW.match(line[1:]) if line[:1] in "+-" else None
        if m:
            (new if line[0] == "+" else old)[m.group(1)] = cells(m.group(2))
        elif line.startswith("+") and is_table_line(line[1:]) and len(tokens(line)) >= 3:
            plain.append((current, line[1:]))
            header_at = len(plain) - 1
    touched = set(git(root, "diff", "--name-only", base).split())
    touched |= set(git(root, "ls-files", "--others", "--exclude-standard", "docs").split())
    for f in git(root, "ls-files", "--others", "--exclude-standard", "--", spec).split():
        for line in (root / f).read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if m:
                new[m.group(1)] = cells(m.group(2))
    return old, new, touched, plain


def check_pack(root: Path, path: Path, rules: Rules, cfg: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for title in PACK_SECTIONS:
        if not re.search(r"^## " + re.escape(title) + r"\s*$", text, re.M):
            err("Q1", f"pack without the section '## {title}'")
    if not re.search(r"^Base: \S+", text, re.M):
        err("Q1", "pack without the line 'Base: <commit>'")
    literal = 0
    for title in ["Rules", "Rows without ID"]:
        for rel, line in literal_rows(section(text, title)):
            f = root / rel
            if not f.exists():
                err("Q1", f"pack cites a missing file: {rel}")
                continue
            m = ROW.match(line)
            if m:
                rid = m.group(1)
                if rid not in rules:
                    err("Q1", f"{rid} does not exist in the PRD")
                elif rules[rid][0].resolve() != f.resolve():
                    err("Q1", f"{rid} is in {rules[rid][0].name}, not in {rel}")
                elif tokens(cells(m.group(2))[0]) != tokens(rules[rid][1][0]):
                    err("Q1", f"{rid}: the pack row is not literal (paraphrase)")
                else:
                    literal += 1
            elif joined(line) not in joined(f.read_text(encoding="utf-8")):
                err("Q1", f"row without ID is not literal in {rel}: {line[:60]}")
            else:
                literal += 1
    if not literal:
        err("Q1", "pack without any literal rule row under '### <file>'")
    trd_rel = cfg["trd_dir"].rstrip("/")
    for rel in re.findall(r"(" + re.escape(trd_rel) + r"/[\w.-]+\.md)", section(text, "TRD")):
        if not (root / rel).exists():
            err("Q1", f"cited TRD does not exist: {rel}")
    inv_path = root / trd_rel / "invariants.md"
    if inv_path.exists():
        known_inv = set(re.findall(r"\|\s*(I-\d+)\s*\|", inv_path.read_text(encoding="utf-8")))
        for inv in re.findall(r"\b(I-\d+)\b", section(text, "Invariants")):
            if inv not in known_inv:
                err("Q1", f"invariant {inv} does not exist in invariants.md")
    size = len(text.splitlines())
    budget = int(cfg["pack_budget_lines"])
    if size > budget:
        warn("Q1", f"pack with {size} lines (budget: {budget})")


def check_rules(path: Path, rules: Rules, cfg: dict[str, str], vias: set[str]) -> None:
    seen: set[str] = set()
    rows = literal_rows(path.read_text(encoding="utf-8"))
    if not rows:
        err("Q2", "no rule row under a '## <file>' or '### <file>'")
    prd_prefix = cfg["prd_dir"].rstrip("/") + "/"
    for rel, line in rows:
        m = ROW.match(line)
        if not m:
            continue
        rid, row = m.group(1), cells(m.group(2))
        if rid in seen:
            err("Q2", f"{rid} repeated")
        seen.add(rid)
        if len(row) < 3 or not row[1] or not row[2]:
            err("Q2", f"{rid} without Source or Change via")
        elif row[2].strip("` ").lower() not in vias:
            err("Q2", f"{rid}: Change via '{row[2]}' outside {sorted(vias)}")
        owner = rules.get(rid)
        if owner and not owner[0].as_posix().endswith(rel.removeprefix(prd_prefix)):
            err("Q2", f"{rid} already exists in {owner[0].name}; do not reuse the ID in {rel}")


def check_html(page_path: Path, rules: Rules, old, new, touched, plain, vias) -> None:
    page = read_html_rules(page_path)
    page_rel = page_path.resolve().as_posix().lower()
    for rid in sorted(set(rules) - set(page)):
        if rid in new:
            err("G5", f"{rid} is in the markdown and missing from the HTML")
        else:
            drift("G5", "in the markdown and not in the HTML", rid)
    for rid in sorted(set(page) - set(rules)):
        if rid in old:
            err("G5", f"{rid} is in the HTML and not in the markdown")
        else:
            drift("G5", "in the HTML and not in the markdown", rid)
    for rid, row in sorted(new.items()):
        if rid in page and tokens(row[0]) != tokens(page[rid]):
            err("G6", f"{rid}: markdown text differs from the HTML")
    if plain:
        page_text = joined(page_path.read_text(encoding="utf-8"))
        for rel, line in plain:
            row = [c for c in cells(line.strip().strip("|")) if c]
            if row and row[0].lower() == "id":
                continue
            if row and row[-1].lower() in vias:
                row = row[:-1]
            if joined(" | ".join(row)) not in page_text:
                err("G10", f"changed table row in {rel} does not appear in the HTML: {line[:70]}")
    names = {t.replace("\\", "/").lstrip("/").lower() for t in touched}
    if (new or old or plain) and not any(page_rel == t or page_rel.endswith("/" + t) for t in names):
        err("G5", "PRD tables changed and the HTML was not touched")


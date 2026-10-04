"""Structural gate of prd-gate: PRD markdown, optional HTML, INDEX, CHANGELOG, TRD and state files.

Configuration comes from the "Gate config" table of ../repo.md.

Usage: python .claude/skills/prd-gate/scripts/gate.py [--base REF]
       python .claude/skills/prd-gate/scripts/gate.py --pack <pack.md>
       python .claude/skills/prd-gate/scripts/gate.py --rules <approved-rules.md>
       python .claude/skills/prd-gate/scripts/gate.py --plan <plan.md>
Exits with 1 when there is an ERROR. A WARNING does not fail.
"""

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

ID = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+[a-z]?"
ROW = re.compile(r"^\|\s*(" + ID + r")(?:\s*·\s*\w+)?\s*\|(.*)\|\s*$")
PIPE = re.compile(r"(?<!\\)\|")
SEPARATOR = re.compile(r"^\|[\s|:-]+$")
HTML_ROW = re.compile(r"<tr[^>]*>\s*<td>(" + ID + r")</td>\s*<td[^>]*>(.*?)</td>", re.S)
RANGE = re.compile(r"([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)-(\d+)(?:\.\.(\d+))?")
EM_DASH = chr(0x2014)
PACK_SECTIONS = ["Rules", "TRD", "Invariants", "Principles", "Divergences", "Pre-interview"]
TASK = re.compile(r"^### (T\d+[a-z]?)\b", re.M)
DEFAULTS = {
    "base_branch": "main",
    "prd_dir": "docs/prd",
    "prd_glob": "*/*.md",
    "trd_dir": "docs/trd",
    "html": "docs/prd/prd.html",
    "forbid_em_dash": "yes",
    "change_via": "code, config, env, prompt, data, backend, frontend",
    "pending_marker": "pending code",
    "planned_source": "planned",
    "pack_budget_lines": "120",
    "plan_budget_kb": "60",
}

errors: list[str] = []
warnings: list[str] = []
baseline: dict[tuple[str, str], list[str]] = {}

Rules = dict[str, tuple[Path, list[str]]]


def err(code: str, msg: str) -> None:
    errors.append(f"ERROR {code} {msg}")


def warn(code: str, msg: str) -> None:
    warnings.append(f"WARNING {code} {msg}")


def drift(code: str, what: str, rid: str) -> None:
    baseline.setdefault((code, what), []).append(rid)


def git(root: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    ).stdout


def load_config() -> dict[str, str]:
    config = dict(DEFAULTS)
    adapter = Path(__file__).resolve().parents[1] / "repo.md"
    if not adapter.exists():
        warn("C1", f"{adapter} not found, using defaults")
        return config
    text = adapter.read_text(encoding="utf-8")
    block = re.search(r"^## Gate config\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not block:
        warn("C1", "repo.md has no '## Gate config' section, using defaults")
        return config
    for line in block.group(1).splitlines():
        m = re.match(r"^\|\s*([a-z_]+)\s*\|\s*(.*?)\s*\|\s*$", line)
        if m and m.group(1) in DEFAULTS:
            config[m.group(1)] = m.group(2).strip("` ")
    return config


def tokens(text: str) -> list[str]:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", " ", text)
    text = html.unescape(text).replace("\\|", "|")
    return re.findall(r"\w+", text.lower())


def joined(text: str) -> str:
    return " " + " ".join(tokens(text)) + " "


def cells(rest: str) -> list[str]:
    return [c.strip() for c in PIPE.split(rest)]


def is_table_line(line: str) -> bool:
    return line.startswith("|") and not SEPARATOR.match(line)


def read_md_rules(prd: Path, pattern: str) -> Rules:
    rules: Rules = {}
    for f in sorted(prd.glob(pattern)):
        for line in f.read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if not m:
                continue
            rid = m.group(1)
            if rid in rules:
                err("G1", f"duplicate ID {rid}: {rules[rid][0].name} and {f.name}")
            rules[rid] = (f, cells(m.group(2)))
    return rules


def read_html_rules(page: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    for m in HTML_ROW.finditer(page.read_text(encoding="utf-8")):
        if m.group(1) in found:
            err("G1", f"duplicate ID in the HTML: {m.group(1)}")
        found[m.group(1)] = m.group(2)
    return found


def expand(spec: str) -> set[str]:
    ids: set[str] = set()
    for prefix, start, end in RANGE.findall(spec):
        width = len(start)
        last = int(end) if end else int(start)
        for n in range(int(start), last + 1):
            ids.add(f"{prefix}-{n:0{width}d}")
    return ids


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
    for line in diff.splitlines():
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
    touched = set(git(root, "diff", "--name-only", base).split())
    touched |= set(git(root, "ls-files", "--others", "--exclude-standard", "docs").split())
    for f in git(root, "ls-files", "--others", "--exclude-standard", "--", spec).split():
        for line in (root / f).read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if m:
                new[m.group(1)] = cells(m.group(2))
    return old, new, touched, plain


def literal_rows(text: str) -> list[tuple[str, str]]:
    found, current = [], ""
    for line in text.splitlines():
        m = re.match(r"^#{2,3} (\S+\.md)\s*$", line)
        if m:
            current = m.group(1)
        elif is_table_line(line.strip()) and current:
            found.append((current, line.strip()))
    return found


def section(text: str, title: str) -> str:
    m = re.search(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


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
        if not re.search(r"^Reviewer:", block, re.M):
            warn("P3", f"{tid} without 'Reviewer:'")
        if not re.search(r"^Model:", block, re.M):
            warn("P4", f"{tid} without 'Model:'")
        for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", block))):
            if rid.rsplit("-", 1)[0] in prefixes and rid not in rules:
                err("P5", f"{tid} cites {rid}, which does not exist in the PRD")


def report(extra: str = "") -> int:
    for (code, what), ids in baseline.items():
        warn(code, f"earlier drift, outside this change, {what}: {', '.join(ids)}")
    for line in [*errors, *warnings]:
        print(line)
    print(f"gate: {len(errors)} error(s), {len(warnings)} warning(s){extra}")
    return 1 if errors else 0


def check_html(page_path: Path, rules: Rules, old, new, touched, plain, vias) -> None:
    page = read_html_rules(page_path)
    page_rel = page_path.as_posix()
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
            if row and row[-1].lower() in vias:
                row = row[:-1]
            if joined(" | ".join(row)) not in page_text:
                err("G10", f"changed table row in {rel} does not appear in the HTML: {line[:70]}")
    if (new or old or plain) and not any(t.endswith(page_rel) for t in touched):
        err("G5", "PRD tables changed and the HTML was not touched")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=None, help="comparison ref; default: merge-base with origin/<base_branch>")
    parser.add_argument("--pack", type=Path, help="check a pack.md from the state folder")
    parser.add_argument("--rules", type=Path, help="check an approved-rules.md from the state folder")
    parser.add_argument("--plan", type=Path, help="check a plan for agents")
    args = parser.parse_args()
    cfg = load_config()
    vias = {v.strip().lower() for v in cfg["change_via"].split(",") if v.strip()}
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip() or ".")
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    prd, trd = root / prd_rel, root / trd_rel
    rules = read_md_rules(prd, cfg["prd_glob"])

    if args.pack or args.rules or args.plan:
        if args.pack:
            check_pack(root, args.pack, rules, cfg)
        if args.rules:
            check_rules(args.rules, rules, cfg, vias)
        if args.plan:
            check_plan(args.plan, rules, cfg)
        return report()

    upstream = f"origin/{cfg['base_branch']}"
    base = args.base or git(root, "merge-base", "HEAD", upstream).strip() or "HEAD"
    old, new, touched, plain = changed_rows(root, base, prd_rel, cfg["prd_glob"])
    check_index(prd, rules, set(new) - set(old))
    changelog = f"{prd_rel}/CHANGELOG.md"
    html_on = cfg["html"].lower() not in {"", "none", "no", "off"}

    if cfg["forbid_em_dash"].lower() in {"yes", "true", "on"}:
        scanned = [*prd.rglob("*.md"), *trd.rglob("*.md")]
        if html_on and (root / cfg["html"]).exists():
            scanned.append(root / cfg["html"])
        for f in scanned:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if EM_DASH in line:
                    err("G4", f"em dash in {f.relative_to(root).as_posix()}:{n}")

    for rid, row in sorted(new.items()):
        if len(row) >= 3 and (not row[1] or not row[2]):
            err("G3", f"{rid} without Source or Change via")
        elif len(row) >= 3 and row[2].strip("` ").lower() not in vias:
            warn("G3", f"{rid}: Change via '{row[2]}' outside {sorted(vias)}")
        if cfg["pending_marker"] in row[0] and len(row) >= 2 and cfg["planned_source"] not in row[1].lower():
            warn("G9", f"{rid} marked '{cfg['pending_marker']}' with Source other than '{cfg['planned_source']}'")
        if rid in old:
            before, after = joined(old[rid][0]), joined(row[0])
            if before not in after and changelog not in touched:
                err("G7", f"{rid} was reworded without a CHANGELOG entry")
    for rid in sorted(set(old) - set(new) - set(rules)):
        if changelog not in touched:
            err("G7", f"{rid} left the PRD without a CHANGELOG entry")
    if set(new) - set(old) and f"{prd_rel}/INDEX.md" not in touched:
        warn("G2", "new IDs and INDEX.md was not touched")

    page_ids: set[str] = set()
    if html_on:
        page_path = root / cfg["html"]
        if page_path.exists():
            check_html(page_path, rules, old, new, touched, plain, vias)
            page_ids = set(read_html_rules(page_path))
        else:
            err("G5", f"html is set to {cfg['html']} and the file does not exist")

    known = set(rules) | page_ids
    for f in trd.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for block in re.findall(r"^## Planned.*?(?=^## |\Z)", text, re.S | re.M):
            for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", block))):
                if not rid.startswith("I-") and rid not in known:
                    err("G8", f"{f.name}: 'Planned' cites {rid}, which does not exist in the PRD")

    return report(f", base {base[:10]}, {len(rules)} rules")


if __name__ == "__main__":
    sys.exit(main())

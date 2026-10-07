"""Shared state, constants and parsing helpers of the gate."""

import html
import re
import subprocess
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
    "planned_heading": "Planned",
    "language": "English",
    "pack_budget_lines": "120",
    "plan_budget_kb": "60",
    "proposed_marker": "proposed",
    "html_mode": "hand",
    "html_template": "docs/templates/prd.html",
    "trd_budget_lines": "250",
}

errors: list[str] = []
warnings: list[str] = []
baseline: dict[tuple[str, str], list[str]] = {}
rule_table_ids: set[str] = set()  # IDs of rows in tables whose header has a "Change via" column

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
    text = re.sub(r"`[^`]*`", lambda m: m.group(0).replace("<", " ").replace(">", " "), text)
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
        is_rule_table = False
        for line in f.read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if not m:
                if not line.startswith("|"):
                    is_rule_table = False
                elif not SEPARATOR.match(line):
                    is_rule_table = "change via" in [c.lower() for c in cells(line.strip().strip("|"))]
                continue
            rid = m.group(1)
            if is_rule_table:
                rule_table_ids.add(rid)
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


def literal_rows(text: str) -> list[tuple[str, str]]:
    found: list[tuple[int, str, str]] = []
    current, dated = "", 0
    for line in text.splitlines():
        if re.match(r"^## \d{4}-\d\d-\d\d", line):
            dated += 1
            current = ""
            continue
        m = re.match(r"^#{2,3} (\S+\.md)\s*$", line)
        if m:
            current = m.group(1)
        elif is_table_line(line.strip()) and current:
            row = ROW.match(line.strip())
            if row:
                found = [x for x in found if not (x[0] < dated and ROW.match(x[2]) and ROW.match(x[2]).group(1) == row.group(1))]
            found.append((dated, current, line.strip()))
    return [(rel, line) for _, rel, line in found]


def ends_with_path(path: Path, rel: str) -> bool:
    parts = Path(rel).parts
    return bool(parts) and path.parts[-len(parts):] == parts


def section(text: str, title: str) -> str:
    m = re.search(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def report(extra: str = "") -> int:
    for (code, what), ids in baseline.items():
        warn(code, f"earlier drift, outside this change, {what}: {', '.join(ids)}")
    for line in [*errors, *warnings]:
        print(line)
    print(f"gate: {len(errors)} error(s), {len(warnings)} warning(s){extra}")
    return 1 if errors else 0



def is_proposed(cell: str, cfg: dict[str, str]) -> bool:
    return f"({cfg['proposed_marker']})" in cell

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
    "via_header": "Change via",
    "language": "English",
    "pack_budget_lines": "120",
    "plan_budget_kb": "60",
    "proposed_marker": "proposed",
    "html_mode": "hand",
    "html_template": "docs/templates/prd.html",
    "trd_budget_lines": "250",
    "prd_section_budget_lines": "200",
}

errors: list[str] = []
warnings: list[str] = []
baseline: dict[tuple[str, str], list[str]] = {}
hints: dict[str, list[str]] = {}
notes: list[str] = []  # plain report lines (wave table), never counted
rule_table_ids: set[str] = set()  # IDs of rows in tables whose header has the via_header column

Rules = dict[str, tuple[Path, list[str]]]


FIXES = {
    "G0": "pass --base with an existing ref (git branch -a lists them)",
    "G1": "rename one of the two rows to a new ID",
    "G2": "add or correct the row in docs/prd/INDEX.md",
    "G3": "fill the Source and Change via cells of the row",
    "G4": "replace the em dash with a comma, colon or period",
    "G5": "rebuild or edit the HTML so it lists the same rules as the markdown",
    "G6": "make the HTML text equal the markdown text",
    "G7": "add a line naming the ID to the PRD CHANGELOG, or revert the text change",
    "G8": "cite an ID that exists in the PRD, or add the rule first",
    "G10": "add the row to the HTML",
    "G11": "point Source at a file that exists",
    "G12": "add a test that cites the ID in its header, or list it in allowlist.untested_rules",
    "G14": "remove the ID from allowlist.untested_rules in ai-kit.json",
    "G15": "cite an ID that exists in the PRD",
    "G16": "add the ID to the Contract of a task in plan.md",
    "G17": "remove the rule row from brief.md and cite its ID",
    "G19": "finish the rule through promote.py, then rerun --final",
    "G20": "remove the Planned section from the TRD file",
    "G21": "promote the change and archive its folder",
    "G22": "create the folder or file, or correct the path",
    "G23": "correct the path in the TRD, or git add the file if it is new",
    "G28": "copy the file between the repositories so both match",
    "G29": "run python .claude/skills/prd-flow/scripts/build_prd_html.py",
    "G30": "approve the rule or drop it",
    "P1": "write the plan as '### TNN' tasks with valid Depends on",
    "P2": "add the Owns: line to the task",
    "P5": "cite an ID that exists in the PRD",
    "P7": "make one of the two tasks depend on the other or give them disjoint Owns",
    "P9": "add the path to the Owns: line of the task",
    "Q1": "rewrite the pack section so it matches the PRD literally",
    "Q2": "fix the row in approved-rules.md",
    "Q3": "rewrite interview.md in the skeleton shown",
    "Q4": "edit the PRD row to equal the approved row",
    "Q5": "add or correct the row of the ID under '## Conflicts' of approved-rules.md",
}


def err(code: str, msg: str, fix: str | None = None) -> None:
    if "; fix: " not in msg:
        msg = f"{msg}; fix: {fix or FIXES.get(code, 'correct it and rerun the gate')}"
    errors.append(f"ERROR {code} {msg}")


def warn(code: str, msg: str) -> None:
    warnings.append(f"WARNING {code} {msg}")


def drift(code: str, what: str, rid: str) -> None:
    baseline.setdefault((code, what), []).append(rid)


def hint(key: str, lines: list[str]) -> None:
    hints.setdefault(key, lines)


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


def read_md_rules(prd: Path, pattern: str, via_header: str = DEFAULTS["via_header"]) -> Rules:
    rules: Rules = {}
    header = via_header.lower()
    for f in sorted(prd.glob(pattern)):
        is_rule_table = False
        for line in f.read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if not m:
                if not line.startswith("|"):
                    is_rule_table = False
                elif not SEPARATOR.match(line):
                    is_rule_table = header in [c.lower() for c in cells(line.strip().strip("|"))]
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
        elif line.startswith("## "):
            current = ""
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


SUPERSEDES = re.compile(r"^[ \t]*[-*]?[ \t]*(" + ID + r")[ \t]*(?:\((.*)\)|:[ \t]*(.*?))[ \t]*$")


def parse_supersedes(body: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in body.splitlines():
        m = SUPERSEDES.match(line)
        if m:
            found[m.group(1)] = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
    return found


def is_proposed(cell: str, cfg: dict[str, str]) -> bool:
    return f"({cfg['proposed_marker']})" in cell


NON_CODE_ROUTES = {"config", "env", "prompt", "data", "backend", "frontend"}


def is_code_route(via: str) -> bool:
    words = [w for w in re.split(r"[^a-z]+", via.lower()) if w]
    return not words or "code" in words or any(w not in NON_CODE_ROUTES for w in words)

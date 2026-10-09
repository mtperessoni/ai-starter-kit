"""The state record of one change: rules.md and delta.md, and the legacy views rendered from them.

rules.md: `# Rules · <slug> · <date> · <approver>`, an optional `Scope:` line, one `## <prd file>.md` section per PRD file
with its current rows (replaced in place), `## Supersedes`, `## Conflicts`, `## Rounds`, `## Decisions` and one or more
`## Dimensions` sections with their `Confirmed:` lines. delta.md: one `| ID | op | files | note |` row per ID and op.
approved-rules.md, interview.md and decisions.md are views of rules.md; without rules.md the legacy files are read as they are.

Usage: python state_record.py render <state dir> [<change dir>]
"""

import re
import sys
from pathlib import Path

RULES = "rules.md"
DELTA = "delta.md"
SPECIAL = re.compile(r"^(Rounds|Decisions|Dimensions)\b", re.I)
HEAD = re.compile(r"^#\s*(?:Rules|Approved rules)\s*·\s*(.*)$")
ID_CELL = re.compile(r"^\|\s*([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+[a-z]?)\b")
DELTA_HEAD = "| ID | op | files | note |\n|---|---|---|---|\n"


def read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.is_file() else None


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def split(text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """The lines before the first `## ` heading, and the sections as (heading line, body lines)."""
    head: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            sections.append((line, []))
        elif sections:
            sections[-1][1].append(line)
        else:
            head.append(line)
    return head, sections


def join(head: list[str], sections: list[tuple[str, list[str]]]) -> str:
    lines = list(head)
    for heading, body in sections:
        lines += [heading, *body]
    return "\n".join(lines).rstrip("\n") + "\n"


def special(heading: str) -> bool:
    return bool(SPECIAL.match(heading[3:].strip()))


def title_parts(head: list[str]) -> str:
    m = HEAD.match(head[0]) if head else None
    return m.group(1).strip() if m else ""


def approved_view(text: str) -> str:
    head, sections = split(text)
    body = [ln for ln in head[1:] if not ln.startswith("Scope:")]
    kept = [(h, b) for h, b in sections if not special(h)]
    return join([f"# Approved rules · {title_parts(head)}", *body], kept)


def interview_view(text: str) -> str:
    head, sections = split(text)
    slug = title_parts(head).split("·")[0].strip()
    scope = [ln for ln in head[1:] if ln.startswith("Scope:")]
    kept = [(h, b) for h, b in sections if h[3:].strip().lower().startswith("dimensions")]
    return join([f"# Interview · {slug}", *scope], kept)


def decision_view(text: str) -> str | None:
    rows = [ln for ln in decision_lines(text)]
    if not rows:
        return None
    head, _ = split(text)
    slug = title_parts(head).split("·")[0].strip()
    return "\n".join([f"# Decisions · {slug}", "",
                      "| ID | Question | Decision | Rejected alternative | Why | Rules |", "|---|---|---|---|---|---|", *rows]) + "\n"


def decision_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if re.match(r"\|\s*DEC-\d+", ln)]


def approved_text(state: Path) -> str | None:
    rules = read(state / RULES)
    return approved_view(rules) if rules is not None else read(state / "approved-rules.md")


def interview_text(state: Path) -> str | None:
    rules = read(state / RULES)
    return interview_view(rules) if rules is not None else read(state / "interview.md")


def decision_rows(state: Path, change: Path | None) -> list[str]:
    rules = read(state / RULES)
    if rules is not None:
        return decision_lines(rules)
    legacy = read(change / "decisions.md") if change else None
    return decision_lines(legacy) if legacy else []


def render_views(state: Path, change: Path | None = None) -> list[Path]:
    """Write approved-rules.md, interview.md and decisions.md from rules.md; the files written, none without rules.md."""
    rules = read(state / RULES)
    if rules is None:
        return []
    out = [(state / "approved-rules.md", approved_view(rules)), (state / "interview.md", interview_view(rules))]
    decisions = decision_view(rules)
    if change is not None and change.is_dir() and decisions:
        out.append((change / "decisions.md", decisions))
    for path, text in out:
        write(path, text)
    return [p for p, _ in out]


def row_id(line: str) -> str | None:
    m = ID_CELL.match(line)
    return m.group(1) if m else None


def replace_rows(state: Path, rows: dict[str, str]) -> int:
    """Replace each rule row of rules.md by ID in place; with only the legacy approved-rules.md, replace there. Rows replaced."""
    path = state / RULES if (state / RULES).is_file() else state / "approved-rules.md"
    text = read(path)
    if text is None:
        return 0
    head, sections = split(text)
    count = 0
    for _, body in sections:
        for i, line in enumerate(body):
            rid = row_id(line)
            if rid in rows and not rid.startswith("DEC-") and body[i] != rows[rid]:
                body[i] = rows[rid]
                count += 1
    write(path, join(head, sections))
    if path.name == RULES:
        render_views(state)
    return count


def upsert_row(state: Path, prd_file: str, line: str) -> None:
    """Replace the row of the same ID, or append it under the section of prd_file (created when missing)."""
    text = read(state / RULES) or "# Rules · slug · date · approver\n"
    head, sections = split(text)
    rid = row_id(line)
    for _, body in sections:
        for i, old in enumerate(body):
            if row_id(old) == rid:
                body[i] = line
                write(state / RULES, join(head, sections))
                return
    for heading, body in sections:
        if heading[3:].strip() == prd_file:
            at = len(body)
            while at and not body[at - 1].strip():
                at -= 1
            body.insert(at, line)
            break
    else:
        first = next((i for i, (h, _) in enumerate(sections) if h[3:].strip() in {"Supersedes", "Conflicts"} or special(h)), len(sections))
        sections.insert(first, (f"## {prd_file}", [line]))
    write(state / RULES, join(head, sections))


def add_round(state: Path, number: int, day: str, summary: str) -> None:
    text = read(state / RULES) or "# Rules · slug · date · approver\n"
    head, sections = split(text)
    row = f"| {number} | {day} | {summary} |"
    for heading, body in sections:
        if heading[3:].strip().lower() == "rounds":
            at = len(body)
            while at and not body[at - 1].strip():
                at -= 1
            body.insert(at, row)
            break
    else:
        sections.append(("## Rounds", ["| Round | Date | Summary |", "|---|---|---|", row]))
    write(state / RULES, join(head, sections))


def append_delta(state: Path, rid: str, op: str, files: str, note: str) -> None:
    """One row per (ID, op): a second call for the same pair replaces the first."""
    text = read(state / DELTA) or DELTA_HEAD
    row = f"| {rid} | {op} | {files} | {note} |"
    lines, done = [], False
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == rid and cells[1] == op:
            lines.append(row)
            done = True
        else:
            lines.append(ln)
    if not done:
        lines.append(row)
    write(state / DELTA, "\n".join(lines).rstrip("\n") + "\n")


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] != "render":
        print(__doc__)
        return 2
    state = Path(argv[2])
    written = render_views(state, Path(argv[3]) if len(argv) > 3 else None)
    print("rendered: " + (", ".join(p.name for p in written) or "nothing (no rules.md)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

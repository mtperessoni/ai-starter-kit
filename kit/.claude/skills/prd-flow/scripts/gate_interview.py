"""Q3: the interview.md beside an approved-rules file covers every dimension and is confirmed."""

import re
from pathlib import Path

from gate_core import Rules, cells, err, is_table_line

STATES = {"user", "doc", "assumed-confirmed", "n/a", "question"}
BASE_DIMENSIONS = [f"D{n:02d}" for n in range(1, 16)]
HEADING = re.compile(r"^## Dimensions\b.*$", re.M)
DIMENSION = re.compile(r"^(D\d+)\b")


def extra_dimensions() -> list[str]:
    adapter = Path(__file__).resolve().parents[1] / "repo.md"
    if not adapter.exists():
        return []
    text = adapter.read_text(encoding="utf-8")
    block = re.search(r"^## Extra interview dimensions\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    found = []
    for line in (block.group(1) if block else "").splitlines():
        if not is_table_line(line) or "<" in line:
            continue
        m = re.match(r"^\|\s*(D\d+)\s*\|", line)
        if m:
            found.append(m.group(1))
    return found


def sections(text: str) -> list[str]:
    parts = HEADING.split(text)
    return parts[1:]


def known_question(qid: str, rules_text: str, prd: Path) -> bool:
    if qid in rules_text:
        return True
    return any(qid in f.read_text(encoding="utf-8", errors="replace") for f in prd.rglob("*.md"))


def check_interview(rules_path: Path, prd: Path, rules: Rules) -> None:
    path = rules_path.parent / "interview.md"
    if not path.exists():
        err("Q3", f"{path.name} not found beside {rules_path.name}")
        return
    blocks = sections(path.read_text(encoding="utf-8"))
    if not blocks:
        err("Q3", "interview.md without a '## Dimensions' table")
        return
    rules_text = rules_path.read_text(encoding="utf-8")
    for n, block in enumerate(blocks):
        seen: set[str] = set()
        for line in block.splitlines():
            if not is_table_line(line.strip()):
                continue
            row = cells(line.strip().strip("|"))
            m = DIMENSION.match(row[0]) if row else None
            if not m or len(row) < 3:
                continue
            dim, state, answer = m.group(1), row[1].strip("` ").lower(), row[2]
            seen.add(dim)
            if state not in STATES:
                err("Q3", f"{dim}: state '{row[1]}' is not one of {sorted(STATES)}")
            elif state == "question":
                qid = re.search(r"\bQ-[\w-]+", answer)
                if not qid:
                    err("Q3", f"{dim}: state question without a Q- ID in Answer")
                elif not known_question(qid.group(0), rules_text, prd):
                    err("Q3", f"{dim}: {qid.group(0)} exists neither in approved-rules.md nor in the PRD")
        if n == 0:
            for dim in [*BASE_DIMENSIONS, *extra_dimensions()]:
                if dim not in seen:
                    err("Q3", f"interview.md without the dimension {dim}")
        elif not seen:
            err("Q3", "a follow-up '## Dimensions' table without any reopened dimension")
        if not re.search(r"^Confirmed:\s*\S", block, re.M):
            err("Q3", "a Dimensions table without a 'Confirmed:' line after it")

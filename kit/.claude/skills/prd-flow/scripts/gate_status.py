"""--status: one line per rule with its state derived from markers and Source."""

from pathlib import Path

from gate_core import Rules, is_proposed
from gate_plan import rule_rows

STATES = ["proposed", "approved", "superseded", "implemented"]


def state_of(row: list[str], cfg: dict[str, str]) -> str:
    if "superseded" in row[0].lower():
        return "superseded"
    if is_proposed(row[0], cfg):
        return "proposed"
    if cfg["pending_marker"] in row[0] or row[1].strip("` ").lower() == cfg["planned_source"]:
        return "approved"
    return "implemented"


def status_lines(rules: Rules, vias: set[str], cfg: dict[str, str], prd: Path, folder: str | None, only: str | None) -> list[str]:
    lines = []
    for rid, row in sorted(rule_rows(rules, vias).items()):
        rel = rules[rid][0].relative_to(prd)
        state = state_of(row, cfg)
        if folder and rel.parts[0] != Path(folder).name:
            continue
        if only and state != only:
            continue
        lines.append(f"{rid} · {state} · {rel.as_posix()} · {row[1].strip('` ')} · {row[2].strip('` ')}")
    return lines

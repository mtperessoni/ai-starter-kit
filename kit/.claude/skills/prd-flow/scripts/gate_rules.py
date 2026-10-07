"""Q4: an approved-rules file applied literally to the PRD."""

from pathlib import Path

from gate_core import ROW, Rules, cells, err, literal_rows


def norm(cell: str) -> str:
    return " ".join(cell.split())


def check_applied(path: Path, rules: Rules, cfg: dict[str, str]) -> None:
    prd_prefix = cfg["prd_dir"].rstrip("/") + "/"
    for rel, line in literal_rows(path.read_text(encoding="utf-8")):
        m = ROW.match(line)
        if not m:
            continue
        rid, row = m.group(1), cells(m.group(2))
        owner = rules.get(rid)
        if not owner:
            err("Q4", f"{rid} is not in the PRD yet")
        elif not owner[0].as_posix().endswith(rel.removeprefix(prd_prefix)):
            err("Q4", f"{rid} is in {owner[0].name}, not in {rel}")
        elif [norm(c) for c in row] != [norm(c) for c in owner[1][: len(row)]]:
            err("Q4", f"{rid}: the PRD row is not identical to the approved row")

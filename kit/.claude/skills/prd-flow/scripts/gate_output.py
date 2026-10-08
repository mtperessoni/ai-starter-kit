"""Gate report: capped stdout, full report in an artifact, scope of --step trd to the files this change touched."""

from pathlib import Path

from gate_core import baseline, errors, git, hints, warn, warnings

MAX_ERRORS = 15
MAX_WARNINGS = 10
STATE_DIR = ".claude/prd-flow/state/_gate"

run = {"mode": "default", "capped": True, "root": None}
outside: dict[str, dict] = {}


def artifact_rel() -> str:
    return f"{STATE_DIR}/last-{run['mode']}.txt"


def start(mode: str, root: Path, capped: bool = True) -> None:
    run.update(mode=mode, root=root, capped=capped)


def base_ref(root: Path, cfg: dict[str, str], base_arg: str | None) -> str:
    return base_arg or git(root, "merge-base", "HEAD", f"origin/{cfg['base_branch']}").strip() or "HEAD"


def changed_trd(root: Path, cfg: dict[str, str], trd_rel: str, base_arg: str | None) -> set[str]:
    base = base_ref(root, cfg, base_arg)
    names = git(root, "-c", "core.quotepath=false", "diff", "--name-only", base).splitlines()
    names += git(root, "-c", "core.quotepath=false", "ls-files", "-m", "-o", "--exclude-standard", "--", trd_rel).splitlines()
    return {n.strip() for n in names if n.strip().startswith(trd_rel + "/")}


def park(code_lines: list[str], rel: str) -> None:
    for line in code_lines:
        code = line.split(" ", 2)[1]
        slot = outside.setdefault(code, {"lines": [], "files": set()})
        slot["lines"].append(line)
        slot["files"].add(rel)


def flush_outside() -> None:
    for code, slot in sorted(outside.items()):
        warn(code, f"earlier drift, outside this change: {len(slot['lines'])} finding(s) in {len(slot['files'])} file(s), see {artifact_rel()}")


def write_artifact(lines: list[str]) -> None:
    root = run["root"]
    if root is None:
        return
    try:
        path = Path(root) / artifact_rel()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        pass


def report(extra: str = "") -> int:
    for (code, what), ids in baseline.items():
        warn(code, f"earlier drift, outside this change, {what}: {', '.join(ids)}")
    flush_outside()
    hint_lines = [f"HINT {line}" for lines in hints.values() for line in lines]
    summary = f"gate:{len(errors)} error(s), {len(warnings)} warning(s){extra}"
    detail = [f"EARLIER {line}" for slot in outside.values() for line in slot["lines"]]
    write_artifact([*errors, *warnings, *detail, *hint_lines, summary])
    shown_errors, shown_warnings = errors, warnings
    cut: list[str] = []
    if run["capped"]:
        shown_errors, shown_warnings = errors[:MAX_ERRORS], warnings[:MAX_WARNINGS]
        cut = [*errors[MAX_ERRORS:], *warnings[MAX_WARNINGS:]]
    for line in [*shown_errors, *shown_warnings]:
        print(line)
    if cut:
        print(f"... {len(cut)} more, see {artifact_rel()}")
    for line in hint_lines:
        print(line)
    print(summary)
    return 1 if errors else 0

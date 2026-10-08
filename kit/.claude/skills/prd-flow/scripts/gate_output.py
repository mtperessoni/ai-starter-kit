"""Gate report: capped stdout, full report in an artifact, scope of --step trd to the files this change touched."""

from pathlib import Path

from gate_core import baseline, err, errors, git, hints, notes, warn, warnings

MAX_ERRORS = 15
MAX_WARNINGS = 10
STATE_DIR = ".claude/prd-flow/state/_gate"

run = {"mode": "default", "capped": True, "root": None}
outside: dict[str, dict] = {}


def artifact_rel() -> str:
    return f"{STATE_DIR}/last-{run['mode']}.txt"


def start(mode: str, root: Path, capped: bool = True) -> None:
    run.update(mode=mode, root=root, capped=capped)


def verified(root: Path, ref: str) -> bool:
    return bool(git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip())


def resolve_base(root: Path, cfg: dict[str, str], base_arg: str | None) -> str:
    if base_arg:
        if verified(root, base_arg):
            return base_arg
        err("G0", f"base ref {base_arg} does not exist")
        return "HEAD"
    name = cfg["base_branch"]
    for ref in (f"origin/{name}", name):
        if verified(root, ref):
            merged = git(root, "merge-base", "HEAD", ref).strip()
            if not merged:
                warn("G0", f"no merge-base with {ref} (shallow clone or unrelated histories), results change after commit")
            return merged or "HEAD"
    warn("G0", f"no base (neither origin/{name} nor {name} exists), results change after commit")
    return "HEAD"


def base_ref(root: Path, cfg: dict[str, str], base_arg: str | None) -> str:
    key = (str(root), base_arg)
    if run.get("base_key") != key:
        run.update(base_key=key, base=resolve_base(root, cfg, base_arg))
    return run["base"]


def changed_paths(root: Path, cfg: dict[str, str], base_arg: str | None) -> set[str]:
    base = base_ref(root, cfg, base_arg)
    names = git(root, "-c", "core.quotepath=false", "diff", "--name-only", base).splitlines()
    names += git(root, "-c", "core.quotepath=false", "ls-files", "-m", "-o", "--exclude-standard").splitlines()
    return {n.strip() for n in names if n.strip()}


def changed_trd(root: Path, cfg: dict[str, str], trd_rel: str, base_arg: str | None) -> set[str]:
    return {n for n in changed_paths(root, cfg, base_arg) if n.startswith(trd_rel + "/")}


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
    write_artifact([*errors, *warnings, *detail, *notes, *hint_lines, summary])
    shown_errors, shown_warnings = errors, warnings
    if run["capped"]:
        shown_errors, shown_warnings = errors[:MAX_ERRORS], warnings[:MAX_WARNINGS]
    for line in [*shown_errors, *shown_warnings]:
        print(line)
    for kind, found, shown in (("errors", errors, shown_errors), ("warnings", warnings, shown_warnings)):
        if len(found) > len(shown):
            print(f"... {len(found) - len(shown)} more {kind}, see {artifact_rel()}")
    for line in notes:
        print(line)
    for line in hint_lines:
        print(line)
    print(summary)
    return 1 if errors else 0

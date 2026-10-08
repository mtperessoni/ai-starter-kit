"""--step plan: waves, critical path (printed, never counted) and P7, P8, P9 from the Owns and Depends on of each task."""

import re
from fnmatch import fnmatchcase
from pathlib import Path

from gate_core import TASK, err, notes, warn

WAVE_SIZE = 4
DOC_PATH = re.compile(r"\b(?:docs|changes)/[\w./-]+")
LABEL = re.compile(r"(?i)\b(creat\w*|consum\w*)\s*:?")


def field(block: str, name: str) -> str:
    m = re.search(r"^" + re.escape(name) + r":[ \t]*(.*)$", block, re.M)
    return m.group(1) if m else ""


def owned(block: str) -> list[str]:
    paths = []
    for part in re.split(r"[,;]", field(block, "Owns")):
        words = part.strip().strip("`").split()
        if words:
            paths.append(words[0].strip("`").rstrip("/"))
    return paths


def created(block: str) -> str:
    text = field(block, "Creates / consumes")
    pieces = LABEL.split(text)
    if len(pieces) == 1:
        return text
    kept = [pieces[0]] if pieces[0].strip() else []
    kept += [pieces[i + 1] for i in range(1, len(pieces) - 1, 2) if pieces[i].lower().startswith("creat")]
    return " ".join(kept)


def parse(text: str) -> dict[str, dict]:
    found = TASK.split(text)
    tasks: dict[str, dict] = {}
    for tid, block in zip(found[1::2], found[2::2], strict=True):
        tasks[tid] = {
            "owns": owned(block),
            "deps": re.findall(r"\bT\d+[a-z]?\b", field(block, "Depends on")),
            "promote": bool(re.match(r"[^\n]*·\s*Promote", block)),
            "creates": created(block),
        }
    return tasks


def shares(a: str, b: str) -> bool:
    """Whether two owned paths or globs can cover the same file: segment by segment, `**` matches any depth."""
    sa, sb = a.split("/"), b.split("/")
    for x, y in zip(sa, sb, strict=False):
        if x == "**" or y == "**":
            return True
        if not (fnmatchcase(y, x) or fnmatchcase(x, y)):
            return False
    return True


def area(paths: list[str]) -> frozenset[str]:
    return frozenset("/".join(p.split("/")[:-1][:3]) or p for p in paths)


def depth(tasks: dict[str, dict]) -> dict[str, int]:
    down: dict[str, int] = {}

    def visit(tid: str, seen: tuple[str, ...]) -> int:
        if tid in down:
            return down[tid]
        children = [c for c, t in tasks.items() if tid in t["deps"] and c not in seen]
        down[tid] = 1 + max((visit(c, (*seen, tid)) for c in children), default=0)
        return down[tid]

    for tid in tasks:
        visit(tid, ())
    return down


def critical_path(tasks: dict[str, dict], down: dict[str, int]) -> list[str]:
    starts = [t for t, v in tasks.items() if not v["deps"]] or list(tasks)
    path = [min(starts, key=lambda t: (-down[t], t))]
    while True:
        nxt = [c for c, v in tasks.items() if path[-1] in v["deps"] and c not in path]
        if not nxt:
            return path
        path.append(min(nxt, key=lambda t: (-down[t], t)))


def make_waves(tasks: dict[str, dict], down: dict[str, int], critical: list[str]) -> list[list[str]] | None:
    done: set[str] = set()
    waves: list[list[str]] = []
    while len(done) < len(tasks):
        ready = [t for t, v in tasks.items() if t not in done and all(d in done for d in v["deps"])]
        if not ready:
            return None
        ready.sort(key=lambda t: (t not in critical, -down[t], t))
        waves.append(ready[:WAVE_SIZE])
        done |= set(ready[:WAVE_SIZE])
    return waves


def check_waves(path: Path) -> None:
    tasks = parse(path.read_text(encoding="utf-8"))
    if not tasks:
        return
    unknown = False
    for tid, task in tasks.items():
        for dep in task["deps"]:
            if dep not in tasks:
                unknown = True
                err("P1", f"{tid} depends on {dep}, which is not a task of the plan", "correct the Depends on: line")
    if unknown:
        return
    down = depth(tasks)
    critical = critical_path(tasks, down)
    waves = make_waves(tasks, down, critical)
    if waves is None:
        err("P1", "the Depends on: lines of the plan form a cycle", "break the cycle so tasks can be ordered")
        return
    for n, wave in enumerate(waves, 1):
        notes.append(f"WAVE {n}: {', '.join(wave)}")
        for i, a in enumerate(wave):
            for b in wave[i + 1:]:
                clash = [(x, y) for x in tasks[a]["owns"] for y in tasks[b]["owns"] if shares(x, y)]
                if clash:
                    err("P7", f"{a} and {b} are in WAVE {n} and both own {clash[0][0]}")
    notes.append(f"CRITICAL PATH: {' > '.join(critical)}")
    for tid, task in tasks.items():
        if task["promote"]:
            continue
        for rel in sorted({p.rstrip(".,;:)") for p in DOC_PATH.findall(task["creates"])}):
            if not any(shares(rel.rstrip("/"), o) for o in task["owns"]):
                err("P9", f"{tid} touches {rel} and does not own it")
        if len(task["deps"]) == 1 and task["deps"][0] in tasks:
            prev = tasks[task["deps"][0]]
            alone = sum(1 for t in tasks.values() if task["deps"][0] in t["deps"]) == 1
            if alone and not prev["promote"] and task["owns"] and area(task["owns"]) == area(prev["owns"]):
                warn("P8", f"{tid} follows {task['deps'][0]} serially in the same area; merge them into one task")

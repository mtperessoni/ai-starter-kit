"""Scope of one change for the final gate (G19 to G21), its snapshot of older drift, and the --docs cache."""

import hashlib
import json
import re
from pathlib import Path

from gate_core import ROW, errors, literal_rows, notes, warnings

STATE = ".claude/prd-flow/state"


def slug_of(change: str) -> str:
    return Path(change.replace("\\", "/")).name


def state_dir(root: Path, slug: str) -> Path:
    return root / STATE / slug


def approved_scope(root: Path, slug: str) -> set[str]:
    path = state_dir(root, slug) / "approved-rules.md"
    if not path.exists():
        return set()
    ids = set()
    for _, line in literal_rows(path.read_text(encoding="utf-8")):
        m = ROW.match(line)
        if m:
            ids.add(m.group(1))
    return ids


def is_change_folder(name: str, slug: str) -> bool:
    return name == slug or name.endswith("-" + slug)


def heading_of_change(heading: str, slug: str) -> bool:
    return re.search(r"\(\s*" + re.escape(slug), heading) is not None


def snapshot_path(root: Path, slug: str) -> Path:
    return state_dir(root, slug) / "final-snapshot.json"


def read_snapshot(root: Path, slug: str) -> set[str]:
    path = snapshot_path(root, slug)
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def write_snapshot(root: Path, slug: str, keys: set[str]) -> Path:
    path = snapshot_path(root, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(keys), indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def inputs_key(root: Path, rels: list[str], extra: str) -> str:
    digest = hashlib.sha256(extra.encode("utf-8"))
    for rel in rels:
        base = root / rel
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
        for f in files:
            if "/_gate/" in f.as_posix():
                continue
            st = f.stat()
            digest.update(f"{f.relative_to(root).as_posix()}|{st.st_mtime_ns}|{st.st_size}\n".encode("utf-8"))
    return digest.hexdigest()


def cache_load(path: Path, key: str) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if data.get("key") == key else None


def cache_store(path: Path, key: str, suffix: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"key": key, "errors": errors, "warnings": warnings, "notes": notes, "suffix": suffix}
        path.write_text(json.dumps(data), encoding="utf-8", newline="\n")
    except OSError:
        pass


def cache_replay(data: dict) -> str:
    errors.extend(data["errors"])
    warnings.extend(data["warnings"])
    notes.extend(data["notes"])
    notes.append("docs: cache hit, inputs unchanged since the last run (--fresh to rerun)")
    return data["suffix"]


def find_plan(root: Path, slug: str) -> Path | None:
    candidates = [state_dir(root, slug) / "plan.md"]
    changes = root / "changes"
    if changes.is_dir():
        candidates += [d / "plan.md" for d in sorted(changes.iterdir()) if d.is_dir() and is_change_folder(d.name, slug)]
    return next((c for c in candidates if c.exists()), None)

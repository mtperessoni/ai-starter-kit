"""The --docs cache and the plan lookup of one change."""

import hashlib
import json
from pathlib import Path

from gate_core import errors, git, notes, warnings

STATE = ".claude/prd-flow/state"


def slug_of(change: str) -> str:
    return Path(change.replace("\\", "/")).name


def state_dir(root: Path, slug: str) -> Path:
    return root / STATE / slug


def is_change_folder(name: str, slug: str) -> bool:
    return name == slug or name.endswith("-" + slug)


def code_state(root: Path) -> str:
    """Hash of the tracked file list, the uncommitted diff and the untracked files, outside the prd-flow state."""
    skip = f":(exclude){STATE}"
    digest = hashlib.sha256()
    digest.update(git(root, "ls-files", "--", ".", skip).encode("utf-8"))
    digest.update(git(root, "diff", "HEAD", "--", ".", skip).encode("utf-8"))
    for rel in git(root, "ls-files", "--others", "--exclude-standard", "--", ".", skip).splitlines():
        try:
            st = (root / rel).stat()
        except OSError:
            continue
        digest.update(f"{rel}|{st.st_mtime_ns}|{st.st_size}|".encode("utf-8"))
    return digest.hexdigest()


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

"""Loads ai-kit.json and walks the repository files it describes."""

import json
import subprocess
from fnmatch import fnmatch
from pathlib import Path


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return Path(out) if out else Path.cwd()


def load(root: Path) -> dict:
    return json.loads((root / "ai-kit.json").read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def matches(relpath: str, patterns: list[str]) -> bool:
    candidate = "/" + relpath
    return any(fnmatch(relpath, p) or fnmatch(candidate, "*/" + p.removeprefix("**/")) for p in patterns)


def is_test(relpath: str, cfg: dict) -> bool:
    return matches(relpath, cfg["test_patterns"])


def code_files(root: Path, cfg: dict) -> list[Path]:
    found: list[Path] = []
    exts = set(cfg["code_extensions"])
    for src in cfg["source_dirs"]:
        base = root / src
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in exts and not matches(rel(p, root), cfg["ignore"]):
                found.append(p)
    return sorted(found)


def test_files(root: Path, cfg: dict) -> list[Path]:
    exts = set(cfg["code_extensions"])
    found = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        r = rel(p, root)
        if r.startswith(".") or matches(r, cfg["ignore"]):
            continue
        if is_test(r, cfg):
            found.append(p)
    return sorted(found)


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def stem(path: Path) -> str:
    name = path.name
    for marker in (".test.", ".spec."):
        if marker in name:
            return name.split(marker)[0]
    return name.split(".")[0]

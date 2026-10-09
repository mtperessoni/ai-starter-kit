"""Loads ai-kit.json and walks the repository files it describes."""

import json
import re
import subprocess
from fnmatch import fnmatchcase
from pathlib import Path


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return Path(out) if out else Path.cwd()


class BaseError(Exception):
    pass


def _ref_exists(root: Path, ref: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],  # noqa: S603, S607
                          capture_output=True, check=False).returncode == 0


def base_branch(root: Path) -> str:
    repo = root / ".claude" / "skills" / "prd-flow" / "repo.md"
    if repo.is_file():
        m = re.search(r"^\|\s*base_branch\s*\|\s*([^|\s]+)\s*\|", repo.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            return m.group(1)
    return "main"


def resolve_base(root: Path, explicit: str | None = None) -> str:
    """The comparison ref: the explicit one if it exists, else origin/<base>, else the local <base>, else BaseError."""
    if explicit:
        if _ref_exists(root, explicit):
            return explicit
        raise BaseError(f"base ref {explicit!r} does not exist: pass --base <existing ref>")
    name = base_branch(root)
    for ref in (f"origin/{name}", name):
        if _ref_exists(root, ref):
            return ref
    raise BaseError(f"neither origin/{name} nor {name} exists: pass --base <ref>")


def load(root: Path) -> dict:
    return json.loads((root / "ai-kit.json").read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().relative_to(root.resolve()).as_posix()


def matches(relpath: str, patterns: list[str]) -> bool:
    candidate = "/" + relpath
    return any(fnmatchcase(relpath, p) or fnmatchcase(candidate, "*/" + p.removeprefix("**/")) for p in patterns)


def is_test(relpath: str, cfg: dict) -> bool:
    return matches(relpath, cfg["test_patterns"])


def is_generated(relpath: str, cfg: dict) -> bool:
    return matches(relpath, cfg.get("generated_patterns", []))


def listed_files(root: Path) -> list[str]:
    """Every file of the work tree, tracked or not yet added, minus the git-ignored: one git call, no per-file resolve."""
    out = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=False,
    )
    if out.returncode == 0 and out.stdout:
        names = sorted({n for n in out.stdout.decode("utf-8", errors="replace").split("\0") if n and (root / n).is_file()})
    else:
        names = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    return names


def code_files(root: Path, cfg: dict) -> list[Path]:
    exts = set(cfg["code_extensions"])
    prefixes = ["" if src in (".", "./", "") else src.strip("/") + "/" for src in cfg["source_dirs"]]
    found = [
        root / r
        for r in listed_files(root)
        if Path(r).suffix in exts and any(r.startswith(p) for p in prefixes) and not matches(r, cfg["ignore"])
    ]
    return sorted(found)


def test_files(root: Path, cfg: dict) -> list[Path]:
    exts = set(cfg["code_extensions"])
    found = []
    for r in listed_files(root):
        if Path(r).suffix not in exts or r.startswith(".") or matches(r, cfg["ignore"]):
            continue
        if is_test(r, cfg):
            found.append(root / r)
    return sorted(found)


def feature_dirs(root: Path, cfg: dict) -> list[Path]:
    base = root / cfg.get("feature_root", "")
    if not cfg.get("feature_root") or not base.is_dir():
        return []
    return sorted(d for d in base.iterdir() if d.is_dir() and not d.name.startswith((".", "_")))


def in_area(relpath: str, root: Path, cfg: dict) -> bool:
    """A file of a product area: under a feature folder, or matched by an area of ai-kit.json "areas"."""
    features = [rel(d, root) + "/" for d in feature_dirs(root, cfg)]
    if any(relpath.startswith(f) for f in features):
        return True
    return any(matches(relpath, globs) for globs in cfg.get("areas", {}).values())


def map_dirs(root: Path, cfg: dict) -> list[str]:
    """Folders that carry a CLAUDE.md map: every feature folder plus ai-kit.json "map_dirs"."""
    found = [rel(d, root) for d in feature_dirs(root, cfg)]
    return sorted(set(found) | set(cfg.get("map_dirs", [])))


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def stem(path: Path) -> str:
    name = path.name
    for marker in (".test.", ".spec."):
        if marker in name:
            return name.split(marker)[0]
    return name.split(".")[0]

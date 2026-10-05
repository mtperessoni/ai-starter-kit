"""EV04: build a fresh evaluation project from the fixture and one kit ref.

python eval/build.py --ref <git ref> --out <dir> [--spec-kit] [--fixture <dir>] [--fill <file>]
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "eval" / "fixture"
CACHE = ROOT / "eval" / ".cache"
SPEC_KIT_TAG = "v1.1.0"
SPEC_KIT_FROM = f"git+https://github.com/github/spec-kit.git@{SPEC_KIT_TAG}"
SPEC_KIT_ARGS = ["--here", "--force", "--non-interactive", "--integration", "claude", "--script", "sh", "--ignore-agent-tools"]

KEEP_IF_PRESENT = ("docs/flow.md", "docs/prd/", "docs/trd/", "docs/adr/README.md")
PROJECT_OWNED = (
    ".claude/skills/prd-gate/repo.md", "docs/code-structure.md", "ai-kit.json", "CLAUDE.md", "AGENTS.md",
    ".specify/memory/constitution.md", ".github/workflows/", ".gitattributes", ".gitleaks.toml",
    "docs/adr/README.md", "docs/flow.md",
)
SCANNED = (
    "CLAUDE.md", "AGENTS.md", "ai-kit.json", ".gitleaks.toml", ".gitattributes", ".github/workflows/",
    ".specify/memory/constitution.md", ".claude/skills/prd-gate/repo.md", "docs/code-structure.md",
    "docs/flow.md", "docs/prd/", "docs/trd/",
)
SYNTAX_TOKENS = {
    "ID", "f", "feature", "file", "slug", "source", "start", "end", "destination", "path", "module",
    "subject", "responsibility", "paths from its TRD file", "prd", "NNN-slug",
}
PLACEHOLDER = re.compile(r"(?<!\$)\{\{[^}\n]*\}\}|<([^<>\n]{2,})>")
GIT_ENV = {
    "GIT_AUTHOR_NAME": "eval", "GIT_AUTHOR_EMAIL": "eval@example.invalid",
    "GIT_COMMITTER_NAME": "eval", "GIT_COMMITTER_EMAIL": "eval@example.invalid",
}


def run(cmd: list[str], cwd: Path, check: bool = True, env: dict[str, str] | None = None) -> str:
    done = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False,
        env={**os.environ, **(env or {})},
    )
    if check and done.returncode:
        raise SystemExit(f"build failed: {' '.join(cmd)}\n{done.stdout}{done.stderr}")
    return done.stdout


def resolve_ref(ref: str) -> str:
    """The ref itself, or `origin/<ref>` when only the remote branch exists (a CI checkout)."""
    for candidate in (ref, f"origin/{ref}"):
        done = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"],
                              cwd=ROOT, capture_output=True)
        if done.returncode == 0:
            return candidate
    raise SystemExit(f"ref not found, locally or on origin: {ref}")


def extract_kit(ref: str, dest: Path) -> Path:
    data = subprocess.run(["git", "archive", ref, "kit"], cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")
    return dest / "kit"


def copy_fixture(out: Path, fixture: Path = FIXTURE) -> None:
    shutil.copytree(
        fixture / "project", out, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )


def snapshot(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def spec_kit_files(fixture: Path = FIXTURE) -> Path:
    suffix = "" if fixture.resolve() == FIXTURE.resolve() else f"-{fixture.resolve().name}"
    cached = CACHE / f"spec-kit-{SPEC_KIT_TAG}{suffix}"
    if cached.exists():
        return cached
    CACHE.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=CACHE))
    try:
        copy_fixture(work, fixture)
        before = snapshot(work)
        run(["uvx", "--from", SPEC_KIT_FROM, "specify", "init", *SPEC_KIT_ARGS], work)
        shutil.rmtree(work / ".git", ignore_errors=True)
        after = snapshot(work)
        added = work.parent / (work.name + "-added")
        for rel, digest in after.items():
            if before.get(rel) != digest:
                target = added / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(work / rel, target)
        try:
            added.rename(cached)
        except OSError:
            shutil.rmtree(added, ignore_errors=True)
            for _ in range(50):
                if cached.exists():
                    break
                time.sleep(0.2)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return cached


def add_spec_kit(out: Path, fixture: Path = FIXTURE) -> None:
    shutil.copytree(spec_kit_files(fixture), out, dirs_exist_ok=True)


def under(rel: str, prefixes: tuple[str, ...]) -> bool:
    return any(rel == p or (p.endswith("/") and rel.startswith(p)) for p in prefixes)


def install_kit(kit: Path, out: Path) -> dict[str, dict[str, str]]:
    files: dict[str, dict[str, str]] = {}
    for src in sorted(p for p in kit.rglob("*") if p.is_file()):
        rel = src.relative_to(kit).as_posix()
        if rel == "gitignore.kit":
            append_missing_lines(out / ".gitignore", src.read_text(encoding="utf-8"))
            continue
        dest = out / rel
        if dest.exists() and under(rel, KEEP_IF_PRESENT):
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        owner = "project" if under(rel, PROJECT_OWNED) else "kit"
        files[rel] = {"owner": owner, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
    if (kit / "docs" / "templates" / "change-brief.md").is_file():
        archive = out / "changes" / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        (archive / ".gitkeep").write_text("", encoding="utf-8")
    return files


def append_missing_lines(path: Path, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    have = set(current.splitlines())
    missing = [line for line in text.splitlines() if line not in have or not line.strip()]
    if current and not current.endswith("\n"):
        current += "\n"
    path.write_text(current + "\n".join(missing) + "\n", encoding="utf-8", newline="\n")


def apply_fill(out: Path, fill_file: Path = FIXTURE / "fill.json") -> None:
    fill = json.loads(fill_file.read_text(encoding="utf-8"))
    for rel, pairs in fill.items():
        path = out / rel
        if not path.exists():
            continue
        text = path.read_bytes().decode("utf-8")
        for literal, value in pairs.items():
            text = text.replace(literal, value)
        path.write_bytes(text.encode("utf-8"))


def find_leftovers(out: Path) -> list[str]:
    found = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and ".git" not in p.relative_to(out).parts):
        rel = path.relative_to(out).as_posix()
        if not under(rel, SCANNED) or path.suffix == ".html":
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in PLACEHOLDER.finditer(line):
                if m.group(1) is None or m.group(1) not in SYNTAX_TOKENS:
                    found.append(f"{rel}:{n}: {m.group(0)[:80]}")
    return found


def write_manifest(out: Path, ref: str, files: dict[str, dict[str, str]]) -> None:
    sha = run(["git", "rev-parse", "--short", ref], ROOT).strip()
    manifest = {
        "kit": {"repo": "local", "version": sha, "installed": "2026-01-05", "updated": "2026-01-05"},
        "stack": {"recipes": ["python"], "package_manager": "pip", "test_runner": "pytest", "ci": "github"},
        "files": files,
    }
    target = out / ".ai-kit" / "manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")


def seed_commit(out: Path) -> None:
    run(["git", "init", "-q", "-b", "main"], out)
    run(["git", "config", "core.autocrlf", "false"], out)
    run(["git", "add", "-A"], out)
    run(["git", "update-index", "--chmod=+x", "scripts/gates.sh"], out, check=False)
    run(["git", "commit", "-q", "-m", "chore: seed"], out, env=GIT_ENV)


def build(ref: str, out: Path, spec_kit: bool, fixture: Path = FIXTURE, fill: Path | None = None) -> None:
    ref = resolve_ref(ref)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    copy_fixture(out, fixture)
    if spec_kit:
        add_spec_kit(out, fixture)
    with tempfile.TemporaryDirectory() as tmp:
        files = install_kit(extract_kit(ref, Path(tmp)), out)
    apply_fill(out, fill or fixture / "fill.json")
    leftovers = find_leftovers(out)
    if leftovers:
        raise SystemExit("placeholders left:\n" + "\n".join(leftovers))
    write_manifest(out, ref, files)
    gate = subprocess.run(
        [sys.executable, ".claude/skills/prd-gate/scripts/gate.py"], cwd=out, capture_output=True, text=True, encoding="utf-8",
    )
    if gate.returncode:
        raise SystemExit("the arm's gate.py fails on the seed:\n" + gate.stdout + gate.stderr)
    seed_commit(out)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--spec-kit", action="store_true")
    parser.add_argument("--fixture", type=Path, default=FIXTURE, help="fixture folder (default eval/fixture)")
    parser.add_argument("--fill", type=Path, help="fill file (default <fixture>/fill.json)")
    args = parser.parse_args(argv)
    args.fill = args.fill or args.fixture / "fill.json"
    return args


def main() -> int:
    args = parse_args()
    build(args.ref, args.out.resolve(), args.spec_kit, args.fixture.resolve(), args.fill.resolve())
    print(f"built {args.out} from {args.ref}{' with spec-kit ' + SPEC_KIT_TAG if args.spec_kit else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Commit trailers: a commit that touches the source folders carries `Rules: <IDs>` or `Case: none (<reason>)`.

Usage: python scripts/commit_trailers.py [<base>..<head>]   default origin/<base_branch>..HEAD (base_branch from repo.md)
Prints the offending commits and exits 1.
"""

import re
import subprocess
import sys

from kit_config import load, repo_root

RULES = re.compile(r"^Rules:\s*\S+", re.MULTILINE)
CASE = re.compile(r"^Case:\s*none\s*\(([^()\n]+)\)\s*$", re.MULTILINE)
MAX_REASON_WORDS = 8
SEP = "\x1e"


def git_run(root, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,  # noqa: S603, S607
                          encoding="utf-8", check=False)


def git(root, *args) -> str:
    return git_run(root, *args).stdout


class GitError(Exception):
    pass


def base_branch(root) -> str:
    repo = root / ".claude" / "skills" / "prd-flow" / "repo.md"
    if repo.is_file():
        m = re.search(r"^\|\s*base_branch\s*\|\s*([^|\s]+)\s*\|", repo.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            return m.group(1)
    return "main"


def has_trailer(body: str) -> bool:
    if RULES.search(body):
        return True
    m = CASE.search(body)
    return bool(m) and len(m.group(1).split()) <= MAX_REASON_WORDS


def offenders(root, rng: str, sources: list[str]) -> list[str]:
    result = git_run(root, "log", "--no-merges", f"--format={SEP}%H%n%s%n%b{SEP}", rng)
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git log {rng} failed")
    log = result.stdout.split(SEP)
    bad = []
    for chunk in log:
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        sha, _, rest = chunk.partition("\n")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            continue
        files = git(root, "diff-tree", "-z", "--no-commit-id", "--name-only", "-r", "--root", sha).split("\0")
        if not any(f == s or f.startswith(s.rstrip("/") + "/") for f in files for s in sources):
            continue
        if not has_trailer(rest):
            bad.append(f"{sha[:8]} {rest.splitlines()[0] if rest else ''}")
    return bad


def main() -> int:
    root = repo_root()
    cfg = load(root)
    rng = sys.argv[1] if len(sys.argv) > 1 else f"origin/{base_branch(root)}..HEAD"
    try:
        bad = offenders(root, rng, cfg["source_dirs"])
    except GitError as e:
        print(f"commit trailers: {e}", file=sys.stderr)
        return 2
    for line in bad:
        print(f"{line}: touches the source folders without a `Rules: <IDs>` or `Case: none (<reason, at most 8 words>)` trailer")
    print(f"commit trailers: {len(bad)} commit(s) without one")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

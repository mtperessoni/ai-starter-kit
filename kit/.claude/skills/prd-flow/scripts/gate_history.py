"""gate.py --history <ID>: the history of one rule from git (S2). The commit body is the record."""

import re
from pathlib import Path

from gate_core import git

FIELDS = ("Request:", "Decided:", "Assumed:")
SEP = "\x1e"


def commits_of(root: Path, rid: str, prd_rel: str) -> list[str]:
    """Hashes, newest first, of commits whose diff touched a PRD row of the ID or whose Rules: trailer names it."""
    row = rf"^\|\s*{re.escape(rid)}\s*(\||·)"
    touched = git(root, "log", "--format=%H", "-G", row, "--", prd_rel).split()
    named = git(root, "log", "--format=%H", "-E", "--grep", rf"^Rules:.*(^|[^A-Za-z0-9-]){re.escape(rid)}($|[^0-9a-z])").split()
    wanted = set(touched) | set(named)
    return [h for h in git(root, "log", "--format=%H").split() if h in wanted]


def describe(root: Path, sha: str) -> list[str]:
    raw = git(root, "log", "-1", "--format=%ad" + SEP + "%h" + SEP + "%s" + SEP + "%b", "--date=short", sha)
    date, short, subject, body = raw.split(SEP, 3)
    lines = [f"{date} {short} {subject}"]
    lines += [f"    {x.strip()}" for x in body.splitlines() if x.strip().startswith(FIELDS)]
    return lines


def history(root: Path, rid: str, prd_rel: str) -> list[str]:
    shas = commits_of(root, rid, prd_rel)
    if not shas:
        return [f"no commit touched or names {rid}"]
    out: list[str] = []
    for sha in shas:
        out += describe(root, sha)
    return out

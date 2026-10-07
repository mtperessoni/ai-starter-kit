"""G27: IDs and change numbers already used on a remote branch. Silent without remotes, never fails the run."""

import re
from pathlib import Path

from gate_core import ID, git, warn

ERE_ID = r"[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]+[a-z]?"
REFS = ("for-each-ref", "--sort=-committerdate", "--count=30", "--format=%(refname)", "refs/remotes")


def remote_refs(root: Path) -> list[str]:
    try:
        return [r for r in git(root, *REFS).split() if not r.endswith("/HEAD")]
    except OSError:
        return []


def warn_remote_ids(root: Path, prd_rel: str, new_ids: set[str]) -> None:
    refs = remote_refs(root) if new_ids else []
    for ref in refs:
        try:
            files = git(root, "grep", "-h", "-o", "-w", "-E", ERE_ID, ref, "--", prd_rel)
        except OSError:
            continue
        for rid in sorted(new_ids & set(re.findall(ID, files))):
            warn("G27", f"{rid} already exists in {prd_rel} on {ref.removeprefix('refs/remotes/')}")


def warn_remote_change(root: Path, folder: Path) -> None:
    m = re.match(r"^(\d+)-", folder.name)
    if not m:
        return
    for ref in remote_refs(root):
        try:
            names = git(root, "ls-tree", "-d", "--name-only", ref, "changes/").split()
        except OSError:
            continue
        for name in names:
            leaf = name.rsplit("/", 1)[-1]
            if leaf.startswith(m.group(1) + "-") and leaf != folder.name:
                warn("G27", f"change number {m.group(1)} is already used by {leaf} on {ref.removeprefix('refs/remotes/')}")

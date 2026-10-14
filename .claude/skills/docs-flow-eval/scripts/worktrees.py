"""Create and remove the eval worktrees of one scenario, safely.

Usage:
  python worktrees.py setup <scenario.json> <run> [<run> ...] [--from <branch>] [--no-fixtures]
  python worktrees.py teardown <scenario.json> <run> [<run> ...]
  python worktrees.py alias <scenario.json> <alias>=<run> [...]   (blind reader aliases)

A run lives in <root>/<scenario>/<run> on branch eval/<scenario>/<run> (kept after teardown, so the
commits stay inspectable). node_modules is a junction (symlink elsewhere) to the scenario repo's own,
and teardown removes that link BEFORE `git worktree remove --force`, which would otherwise delete
the real node_modules through it. Setup copies the frozen survey (fixtures/) into the prd-flow state.
Root: env DOCS_EVAL_ROOT, default C:/Projects/ab-eval.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("DOCS_EVAL_ROOT", "C:/Projects/ab-eval"))


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True)


def link(dst: Path, src: Path) -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(dst).replace("/", "\\"), str(src).replace("/", "\\")], check=True, capture_output=True)
    else:
        dst.symlink_to(src, target_is_directory=True)


def unlink(p: Path) -> None:
    if not os.path.lexists(p):
        return
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "rmdir", str(p).replace("/", "\\")], check=True, capture_output=True)
    else:
        p.unlink()


def main() -> None:
    action, sc_path, *rest = sys.argv[1:]
    sc_file = Path(sc_path)
    sc = json.loads(sc_file.read_text(encoding="utf-8"))
    repo = Path(sc["repo"])
    home = ROOT / sc["name"]
    from_ref = sc["base"]
    fixtures = True
    if "--from" in rest:
        i = rest.index("--from")
        from_ref = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    if "--no-fixtures" in rest:
        rest.remove("--no-fixtures")
        fixtures = False

    if action == "setup":
        home.mkdir(parents=True, exist_ok=True)
        for run in rest:
            wt = home / run
            branch = f"eval/{sc['name']}/{run}"
            if from_ref == sc["base"]:
                git(repo, "worktree", "add", "-q", "-b", branch, str(wt), from_ref)
            else:
                git(repo, "worktree", "add", "-q", str(wt), from_ref)
            link(wt / "node_modules", repo / "node_modules")
            src = sc_file.parent / sc["fixtures"]
            if fixtures and src.is_dir() and any(src.iterdir()):
                state = wt / ".claude/prd-flow/state" / sc["slug"]
                state.mkdir(parents=True, exist_ok=True)
                for f in src.iterdir():
                    text = f.read_text(encoding="utf-8").replace("{WORKTREE}", wt.as_posix())
                    (state / f.name).write_text(text, encoding="utf-8")
            print(f"ready {wt}")
    elif action == "alias":
        for pair in rest:
            alias, run = pair.split("=")
            link(home / alias, home / run)
            print(f"alias {alias} -> {run}")
    elif action == "teardown":
        for run in rest:
            wt = home / run
            if not wt.exists():
                continue
            if wt.is_junction() if hasattr(wt, "is_junction") else False:
                unlink(wt)
                continue
            unlink(wt / "node_modules")
            if not (repo / "node_modules").is_dir():
                sys.exit(f"STOP: {repo / 'node_modules'} is missing after unlinking {run}")
            git(repo, "worktree", "remove", "--force", str(wt))
            print(f"removed {wt} (branch kept)")
        git(repo, "worktree", "prune")
        if home.is_dir() and not any(home.iterdir()):
            home.rmdir()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

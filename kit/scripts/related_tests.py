"""Related tests of a change (rule TS02): the mirror test of each changed module and the tests that import it.

Usage: python scripts/related_tests.py [files...] [--base REF] [--run]
Without files, the change is: committed since the merge-base with REF (default origin/main), plus
uncommitted and untracked files. --run executes them with tests.runner from ai-kit.json (or
tests.native_related when set), writes the log to tests.log_dir and prints only failures and the summary.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from kit_config import is_test, load, rel, repo_root, stem, test_files

IMPORT_LINE = re.compile(r"^\s*(import|from|require|use|using|include|#include|export)\b|require\(|import\(", re.M)


def git_lines(root: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False).stdout  # noqa: S603,S607
    return [line for line in out.splitlines() if line.strip()]


def changed_files(root: Path, base: str) -> list[str]:
    merge_base = (git_lines(root, "merge-base", "HEAD", base) or ["HEAD"])[0]
    files = set(git_lines(root, "diff", "--name-only", merge_base))
    files |= set(git_lines(root, "ls-files", "--others", "--exclude-standard"))
    return sorted(f for f in files if (root / f).exists())


def mirror_names(module_stem: str) -> set[str]:
    return {f"test_{module_stem}", f"{module_stem}_test", f"{module_stem}_spec", module_stem}


def imports_module(text: str, module: Path, root: Path) -> bool:
    relpath = rel(module, root)
    no_ext = relpath.rsplit(".", 1)[0]
    parts = no_ext.split("/")
    tail = parts[-2:] if len(parts) > 1 else parts
    forms = {"/".join(tail), ".".join(tail)}
    name = stem(module)
    for line in text.splitlines():
        if not IMPORT_LINE.search(line):
            continue
        if any(form in line for form in forms):
            return True
        if re.search(r"[./'\"\s]" + re.escape(name) + r"\b", line):
            return True
    return False


def related(root: Path, cfg: dict, changed: list[str]) -> list[str]:
    tests = test_files(root, cfg)
    exts = set(cfg["code_extensions"])
    picked: set[str] = set()
    modules = []
    for f in changed:
        p = root / f
        if p.suffix not in exts:
            continue
        if is_test(f, cfg):
            picked.add(f)
        else:
            modules.append(p)
    contents = {t: t.read_text(encoding="utf-8", errors="replace") for t in tests}
    for module in modules:
        names = mirror_names(stem(module))
        for t in tests:
            r = rel(t, root)
            if stem(t) in names or imports_module(contents[t], module, root):
                picked.add(r)
    return sorted(picked)


def run(root: Path, cfg: dict, files: list[str], changed: list[str]) -> int:
    native = cfg["tests"].get("native_related", "")
    if native:
        command = native.replace("{changed}", " ".join(changed))
    elif files:
        command = cfg["tests"]["runner"].replace("{files}", " ".join(files))
    else:
        print("related: no related tests")
        return 0
    log_dir = root / cfg["tests"]["log_dir"]
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / "related.log"
    with log.open("w", encoding="utf-8") as out:
        code = subprocess.run(command, shell=True, cwd=root, stdout=out, stderr=subprocess.STDOUT, check=False).returncode  # noqa: S602
    failure = re.compile(cfg["tests"]["failure_regex"])
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        if failure.search(line):
            print(line)
    print(lines[-1] if lines else "(empty log)")
    print(f"related: exit {code}, full log in {rel(log, root)}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    cfg = load(root)
    changed = args.files or changed_files(root, args.base)
    files = related(root, cfg, changed)
    if args.run:
        return run(root, cfg, files, changed)
    for f in files:
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())

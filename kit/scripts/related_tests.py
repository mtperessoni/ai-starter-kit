"""Related tests of a change (rule TS02): the mirror test of each changed module and the tests that use it.

Usage: python scripts/related_tests.py [files...] [--base REF] [--run]
Without files, the change is: committed since the merge-base with REF (default origin/main), plus
uncommitted and untracked files. --run executes them with tests.runner from ai-kit.json (or
tests.native_related when set), writes the log to tests.log_dir and prints only failures, the summary,
the wall time against tests.related_budget_seconds (TS37) and, with tests.junit_xml, the slowest tests.
A mirror test is named by tests.mirror_patterns; a test uses a module when an import line names it or, with
tests.match_symbol, when it names the module as a word (languages whose imports name namespaces or autoload).
"""

import argparse
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from kit_config import is_test, load, matches, rel, repo_root, stem, test_files

IMPORT_LINE = re.compile(r"^\s*(import|from|require|use|using|include|#include|export)\b|require\(|import\(", re.M)
COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*|--|;|%|')")
DEFAULT_MIRRORS =["test_{name}", "{name}_test", "{name}_spec", "{name}.test", "{name}.spec"]
SLOWEST = 5


def git_lines(root: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False).stdout  # noqa: S603,S607
    return [line for line in out.splitlines() if line.strip()]


def changed_files(root: Path, base: str) -> list[str]:
    merge_base = (git_lines(root, "merge-base", "HEAD", base) or ["HEAD"])[0]
    files = set(git_lines(root, "diff", "--name-only", merge_base))
    files |= set(git_lines(root, "ls-files", "--others", "--exclude-standard"))
    return sorted(f for f in files if (root / f).exists())


def base_names(module: Path) -> set[str]:
    return {stem(module), module.name.rsplit(".", 1)[0]}


def mirror_names(module: Path, cfg: dict) -> set[str]:
    patterns = cfg["tests"].get("mirror_patterns", DEFAULT_MIRRORS)
    names = set()
    for base in base_names(module):
        names.add(base)
        names |= {p.replace("{name}", base) for p in patterns}
    return names


def test_name(path: Path) -> str:
    return path.name.rsplit(".", 1)[0]


def symbol_forms(module: Path) -> set[str]:
    """Identifier-shaped names only: a bare lowercase word such as `order` would select every test that says it."""
    forms = set()
    for base in base_names(module):
        if re.search(r"[A-Z_.]", base):
            forms.add(base)
        forms.add("".join(part[:1].upper() + part[1:] for part in re.split(r"[_.-]", base) if part))
    return forms


def imports_module(text: str, module: Path, root: Path) -> bool:
    relpath = rel(module, root)
    no_ext = relpath.rsplit(".", 1)[0]
    parts = no_ext.split("/")
    tail = parts[-2:] if len(parts) > 1 else parts
    forms = {"/".join(tail), ".".join(tail), "\\".join(tail)}
    name = stem(module)
    for line in text.splitlines():
        if not IMPORT_LINE.search(line):
            continue
        if any(form in line for form in forms):
            return True
        if re.search(r"[./\\'\"\s]" + re.escape(name) + r"\b", line):
            return True
    return False


def names_symbol(text: str, module: Path, cfg: dict) -> bool:
    exempt = {n.lower() for n in cfg["unique_name_exempt"]}
    forms = [f for f in symbol_forms(module) if f.lower() not in exempt]
    code = "\n".join(line for line in text.splitlines() if not COMMENT_LINE.match(line))
    return any(re.search(r"\b" + re.escape(form) + r"\b", code) for form in forms)


def related(root: Path, cfg: dict, changed: list[str]) -> list[str]:
    tests = test_files(root, cfg)
    exts = set(cfg["code_extensions"])
    match_symbol = cfg["tests"].get("match_symbol", False)
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
        names = mirror_names(module, cfg)
        for t in tests:
            text = contents[t]
            if test_name(t) in names or stem(t) in names or imports_module(text, module, root):
                picked.add(rel(t, root))
            elif match_symbol and names_symbol(text, module, cfg):
                picked.add(rel(t, root))
    return sorted(picked)


def snapshot_warnings(cfg: dict, changed: list[str]) -> list[str]:
    patterns = cfg["tests"].get("snapshot_patterns", [])
    return [
        f"snapshot changed: {f} (TS39: only for a PRD ID that changed the expected output; name it in the return)"
        for f in changed
        if matches(f, patterns)
    ]


def slowest_tests(root: Path, pattern: str) -> list[str]:
    reports = sorted(p for p in root.glob(pattern) if p.is_file())
    cases = []
    for report in reports:
        try:
            tree = ET.parse(report)  # noqa: S314
        except (ET.ParseError, OSError) as error:
            print(f"slowest: skipped {rel(report, root)} ({error})")
            continue
        for case in tree.getroot().iter("testcase"):
            seconds = float(case.get("time") or 0)
            cases.append((seconds, f"{case.get('classname', '')}.{case.get('name', '')}"))
    return [f"{seconds:.2f} s {name}" for seconds, name in sorted(cases, reverse=True)[:SLOWEST]]


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
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as out:
        code = subprocess.run(command, shell=True, cwd=root, stdout=out, stderr=subprocess.STDOUT, check=False).returncode  # noqa: S602
    elapsed = time.monotonic() - started
    failure = re.compile(cfg["tests"]["failure_regex"])
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        if failure.search(line):
            print(line)
    print(lines[-1] if lines else "(empty log)")
    budget = cfg["tests"].get("related_budget_seconds")
    over = f", over the budget of {budget} s: split the slow test or its fixture (TS37)" if budget is not None and elapsed > budget else ""
    print(f"related: {elapsed:.1f} s{over}")
    report = cfg["tests"].get("junit_xml", "")
    if report:
        for line in slowest_tests(root, report):
            print(f"slowest: {line}")
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
    for warning in snapshot_warnings(cfg, changed):
        print(warning)
    files = related(root, cfg, changed)
    if args.run:
        return run(root, cfg, files, changed)
    for f in files:
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())

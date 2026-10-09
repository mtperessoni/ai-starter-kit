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
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from kit_config import BaseError, is_test, listed_files, load, matches, rel, repo_root, resolve_base, stem, test_files

IMPORT_LINE = re.compile(r"^\s*(import|from|require|use|using|include|#include|export)\b|require\(|import\(", re.M)
COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*|--|;|%|')")
DEFAULT_MIRRORS =["test_{name}", "{name}_test", "{name}_spec", "{name}.test", "{name}.spec"]
SLOWEST = 5
MAX_FILES = 60
CMD_CHARS = 7000
NO_BARE_STEM = {"__init__", "index"}


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


def dotted_forms(parts: list[str]) -> set[str]:
    if len(parts) == 1:
        return {parts[0]}
    return {".".join(parts[i:]) for i in range(len(parts) - 1)}


def imports_module(text: str, module: Path, root: Path, packages: frozenset[str] = frozenset()) -> bool:
    """A line imports the module by its dotted path (Python) or its trailing path, never by a stem that is also a package name."""
    parts = rel(module, root).rsplit(".", 1)[0].split("/")
    name = stem(module)
    if name == "__init__":
        return False
    python = module.suffix == ".py"
    if python:
        forms = dotted_forms(parts)
    else:
        tail = parts[-2:]
        forms = {"/".join(tail), ".".join(tail), "\\".join(tail)}
    bare = not python and name not in NO_BARE_STEM and name not in packages
    parent = ".".join(parts[:-1])
    for line in text.splitlines():
        if not IMPORT_LINE.search(line):
            continue
        if python:
            if any(re.search(r"(?<!\w)" + re.escape(form) + r"(?!\w)", line) for form in forms):
                return True
            m = re.match(r"\s*from\s+\.*([\w.]*)\s+import\s+(.+)", line)
            if m and name in re.findall(r"\w+", m.group(2)) and m.group(1) and (parent == m.group(1) or parent.endswith("." + m.group(1))):
                return True
        elif any(form in line for form in forms):
            return True
        if bare and re.search(r"[./\'\"\s]" + re.escape(name) + r"", line):
            return True
    return False


def names_symbol(text: str, module: Path, cfg: dict) -> bool:
    exempt = {n.lower() for n in cfg["unique_name_exempt"]}
    forms = [f for f in symbol_forms(module) if f.lower() not in exempt]
    code = "\n".join(line for line in text.splitlines() if not COMMENT_LINE.match(line))
    return any(re.search(r"\b" + re.escape(form) + r"\b", code) for form in forms)


def owning_test_folder(module: Path, root: Path, test_rels: list[str]) -> str:
    """The deepest ancestor folder of the module that holds tests, else the common folder of the mirror tests."""
    folder = Path(rel(module, root)).parent
    while str(folder) != ".":
        prefix = folder.as_posix() + "/"
        if any(t.startswith(prefix) for t in test_rels):
            return prefix
        folder = folder.parent
    return ""


def related(root: Path, cfg: dict, changed: list[str]) -> list[str]:
    tests = test_files(root, cfg)
    test_rels = [rel(t, root) for t in tests]
    exts = set(cfg["code_extensions"])
    match_symbol = cfg["tests"].get("match_symbol", False)
    cap = cfg["tests"].get("related_max_files", MAX_FILES)
    packages = frozenset(part for f in listed_files(root) for part in f.split("/")[:-1])
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
            if test_name(t) in names or stem(t) in names or imports_module(text, module, root, packages):
                picked.add(rel(t, root))
            elif match_symbol and names_symbol(text, module, cfg):
                picked.add(rel(t, root))
    folders = {owning_test_folder(m, root, test_rels) for m in modules} - {""}
    if len(picked) > cap and folders:
        print(
            f"related: {len(picked)} tests selected, over the cap of {cap} (tests.related_max_files): "
            f"running the owning test folder {sorted(folders)} instead",
            file=sys.stderr,
        )
        picked = {f for f in picked if is_test(f, cfg) and f in changed}
        picked |= {t for t in test_rels if any(t.startswith(folder) for folder in folders)}
    elif len(picked) > cap:
        print(
            f"related: {len(picked)} tests selected, over the cap of {cap} (tests.related_max_files): "
            "no owning test folder, running the mirror tests and the structure tests only",
            file=sys.stderr,
        )
        mirrors = {rel(t, root) for t in tests if any(test_name(t) in mirror_names(m, cfg) or stem(t) in mirror_names(m, cfg) for m in modules)}
        picked = {f for f in picked if f in changed} | mirrors
    picked |= always_files(root, cfg)
    exclude = cfg["tests"].get("related_exclude", [])
    return sorted(f for f in picked if not matches(f, exclude))


def always_files(root: Path, cfg: dict) -> set[str]:
    found: set[str] = set()
    for pattern in cfg["tests"].get("always", []):
        found |= {f for f in listed_files(root) if matches(f, [pattern])}
    return found


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


def split_command(command: str) -> list[str]:
    if os.name != "nt":
        return shlex.split(command)
    return [t[1:-1] if len(t) > 1 and t[0] == t[-1] and t[0] in "\"'" else t for t in shlex.split(command, posix=False)]


def chunked_commands(template: str, placeholder: str, items: list[str], limit: int) -> list[list[str]]:
    """The argv lists of a runner template, the items spread so no command line passes `limit` characters (Windows caps at 8,191)."""
    argv = split_command(template)
    if placeholder not in " ".join(argv):
        return [argv]
    fixed = sum(len(t) + 1 for t in argv if placeholder not in t)
    chunks: list[list[str]] = [[]]
    size = fixed
    for item in items:
        if chunks[-1] and size + len(item) + 3 > limit:
            chunks.append([])
            size = fixed
        chunks[-1].append(item)
        size += len(item) + 3
    commands = []
    for chunk in chunks:
        expanded = []
        for token in argv:
            if token == placeholder:
                expanded += chunk
            else:
                expanded.append(token.replace(placeholder, " ".join(chunk)))
        commands.append(expanded)
    return commands


def selection_key(root: Path, cfg: dict, files: list[str], changed: list[str]) -> str:
    digest = hashlib.sha256(json.dumps([cfg["tests"].get("runner"), cfg["tests"].get("native_related")]).encode())
    for f in sorted(set(files) | set(changed)):
        path = root / f
        digest.update(f.encode())
        digest.update(path.read_bytes() if path.is_file() else b"<missing>")
    return digest.hexdigest()


def run(root: Path, cfg: dict, files: list[str], changed: list[str]) -> int:
    native = cfg["tests"].get("native_related", "")
    exts = set(cfg["code_extensions"])
    changed = [f for f in changed if Path(f).suffix in exts]
    always = always_files(root, cfg) & set(files)
    plan = []
    if native:
        plan.append((native, "{changed}", changed, True))
        if always:
            plan.append((cfg["tests"]["runner"], "{files}", sorted(always), False))
    elif files:
        plan.append((cfg["tests"]["runner"], "{files}", [f for f in files if f not in always], True))
        if always:
            plan.append((cfg["tests"]["runner"], "{files}", sorted(always), False))
        plan = [entry for entry in plan if entry[2]]
    else:
        print("related: no related tests")
        return 0
    log_dir = root / cfg["tests"]["log_dir"]
    log_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w.-]", "-", os.environ.get("AI_KIT_CONTEXT", "").strip())
    suffix = f"-{slug}" if slug else ""
    log = log_dir / f"related{suffix}.log"
    cache = log_dir / f"related.cache{suffix}.json"
    key = selection_key(root, cfg, files, changed)
    try:
        saved = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    if saved.get("key") == key:
        print("related: unchanged since the last run (same selection and file hashes), cached summary:")
        for line in saved["lines"]:
            print(line)
        return 0
    limit = cfg["tests"].get("related_cmd_chars", CMD_CHARS)
    elapsed = 0.0
    code = 0
    with log.open("w", encoding="utf-8") as out:
        for template, placeholder, items, timed in plan:
            for argv in chunked_commands(template, placeholder, items, limit):
                argv[0] = shutil.which(argv[0]) or argv[0]
                started = time.monotonic()
                returned = subprocess.run(argv, shell=False, cwd=root, stdout=out, stderr=subprocess.STDOUT, check=False).returncode  # noqa: S603
                if timed:
                    elapsed += time.monotonic() - started
                code = code or returned
    failure = re.compile(cfg["tests"]["failure_regex"])
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    summary = [line for line in lines if failure.search(line)] + [lines[-1] if lines else "(empty log)"]
    for line in summary:
        print(line)
    if code == 0 and not any(failure.search(line) for line in lines):
        cache.write_text(json.dumps({"key": key, "lines": summary}), encoding="utf-8")
    elif cache.exists():
        cache.unlink()
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
    parser.add_argument("--base", default=None)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--args-file", default=None, help="a file with one changed path per line")
    args = parser.parse_args()
    root = repo_root()
    cfg = load(root)
    given = list(args.files)
    if args.args_file:
        given += [line.strip() for line in Path(args.args_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    try:
        changed = given or changed_files(root, resolve_base(root, args.base))
    except BaseError as e:
        print(f"related: ERROR {e}", file=sys.stderr)
        return 2
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

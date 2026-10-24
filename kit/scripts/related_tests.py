"""Related tests of a change: the mirror test of each changed module and the tests that use it.

Usage: python scripts/related_tests.py [files...] [--base REF] [--run] [--with-always]
Without files, the change is the uncommitted and untracked files; with --base REF it also holds everything committed
since the merge-base with REF. tests.always files join the selection only with --with-always (the slice closing,
gates.sh verify). A selection over half of all test files runs the whole suite instead. {python} in a runner
template is the interpreter running this script. --run executes them with tests.runner from ai-kit.json (or
tests.native_related when set), writes the log to tests.log_dir and prints only failures, the summary,
the wall time against tests.related_budget_seconds (TS37) and, with tests.junit_xml, the slowest tests.
A selection of tests.parallel_from files or more runs with tests.parallel_runner when set, and so does a selection
over tests.related_max_files instead of the owning-folder fallback; tests.runner_args_file hands the selection to
one call as @file (pytest 8.2 and later) instead of chunked command lines.
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
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

from kit_config import BaseError, is_test, listed_files, load, matches, rel, repo_root, resolve_base, stem, test_files

IMPORT_LINE = re.compile(r"^\s*(import|from|require|use|using|include|#include|export)\b|require\(|import\(", re.M)
COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*|--|;|%|')")
DEFAULT_MIRRORS =["test_{name}", "{name}_test", "{name}_spec", "{name}.test", "{name}.spec"]
SLOWEST = 5
MAX_FILES = 60
PARALLEL_FROM = 40
CMD_CHARS = 7000
NO_BARE_STEM = {"__init__", "index"}
WHOLE_SUITE_SHARE = 0.5
FROM_IMPORT = re.compile(r"\s*from\s+\.*([\w.]*)\s+import\s+(.+)")
TOKEN = re.compile(r"[\w.]+")


def git_lines(root: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False).stdout  # noqa: S603,S607
    return [line for line in out.splitlines() if line.strip()]


def changed_files(root: Path, base: str | None) -> list[str]:
    """Uncommitted and untracked files; with a base, also what is committed since the merge-base."""
    merge_base = (git_lines(root, "merge-base", "HEAD", base) or ["HEAD"])[0] if base else "HEAD"
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


class ImportIndex(NamedTuple):
    keys: frozenset
    lines: str
    text: str


def dotted_runs(token: str) -> Iterator[list[str]]:
    run: list[str] = []
    for segment in token.split("."):
        if segment:
            run.append(segment)
        elif run:
            yield run
            run = []
    if run:
        yield run


def import_index_of(text: str, keep_text: bool) -> ImportIndex:
    """The import lines of a test with every contiguous dotted run of their tokens, plus ("from", module, name) per imported name."""
    lines = [line for line in text.splitlines() if IMPORT_LINE.search(line)]
    keys: set = set()
    for line in lines:
        for token in TOKEN.findall(line):
            for run in dotted_runs(token):
                keys.update(".".join(run[i:j]) for i in range(len(run)) for j in range(i + 1, len(run) + 1))
        m = FROM_IMPORT.match(line)
        if m and m.group(1):
            keys.update(("from", m.group(1), word) for word in re.findall(r"\w+", m.group(2)))
    return ImportIndex(frozenset(keys), "\n".join(lines), text if keep_text else "")


def index_imports_module(entry: ImportIndex, module: Path, root: Path, packages: frozenset[str]) -> bool:
    """imports_module over the index: the same answer for a Python module, the line scan for any other language."""
    parts = rel(module, root).rsplit(".", 1)[0].split("/")
    if module.suffix != ".py":
        return imports_module(entry.lines, module, root, packages)
    if stem(module) == "__init__":
        return False
    forms = dotted_forms(parts)
    if not all(TOKEN.fullmatch(form) for form in forms):
        return imports_module(entry.lines, module, root, packages)
    if not forms.isdisjoint(entry.keys):
        return True
    parent = parts[:-1]
    heads = {".".join(parent[i:]) for i in range(len(parent))}
    return any(("from", head, stem(module)) in entry.keys for head in heads)


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


def related(root: Path, cfg: dict, changed: list[str], with_always: bool = False) -> list[str]:
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
    index = {t: import_index_of(t.read_text(encoding="utf-8", errors="replace"), match_symbol) for t in tests} if modules else {}
    for module in modules:
        names = mirror_names(module, cfg)
        for t in tests:
            entry = index[t]
            if test_name(t) in names or stem(t) in names or index_imports_module(entry, module, root, packages):
                picked.add(rel(t, root))
            elif match_symbol and names_symbol(entry.text, module, cfg):
                picked.add(rel(t, root))
    folders = {owning_test_folder(m, root, test_rels) for m in modules} - {""}
    if len(picked) > cap and cfg["tests"].get("parallel_runner"):
        print(
            f"related: {len(picked)} tests selected, over the cap of {cap} (tests.related_max_files): "
            "keeping every importer (tests.parallel_runner is set; tests.parallel_from picks the runner)",
            file=sys.stderr,
        )
    elif len(picked) > cap and folders:
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
    if with_always:
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
    quoted = f'"{sys.executable}"' if " " in sys.executable else sys.executable
    argv = split_command(template.replace("{python}", quoted))
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


def main_runner(cfg: dict, count: int) -> str:
    """tests.parallel_runner from tests.parallel_from selected files on: a small selection is faster in one process."""
    parallel = cfg["tests"].get("parallel_runner", "")
    if parallel and count >= cfg["tests"].get("parallel_from", PARALLEL_FROM):
        return parallel
    return cfg["tests"]["runner"]


def runner_commands(root: Path, cfg: dict, template: str, placeholder: str, items: list[str], list_file: Path) -> list[list[str]]:
    """With tests.runner_args_file the selection goes to one call as @file (pytest 8.2 and later), else chunked argv."""
    if placeholder == "{files}" and cfg["tests"].get("runner_args_file") and placeholder in template:
        list_file.write_text("\n".join(items) + "\n", encoding="utf-8")
        return chunked_commands(template, placeholder, ["@" + rel(list_file, root)], 10**9)
    return chunked_commands(template, placeholder, items, cfg["tests"].get("related_cmd_chars", CMD_CHARS))


def selection_key(root: Path, cfg: dict, files: list[str], changed: list[str]) -> str:
    keys = ("runner", "native_related", "parallel_runner", "parallel_from", "runner_args_file")
    digest = hashlib.sha256(json.dumps([cfg["tests"].get(k) for k in keys]).encode())
    for f in sorted(set(files) | set(changed)):
        path = root / f
        digest.update(f.encode())
        digest.update(path.read_bytes() if path.is_file() else b"<missing>")
    return digest.hexdigest()


def whole_suite_over_half(root: Path, cfg: dict, files: list[str], always: set[str]) -> list[str]:
    """Every test file when the selection holds more than half of them (the selection then saves nothing); else []."""
    every = sorted(rel(t, root) for t in test_files(root, cfg))
    chosen = [f for f in files if f not in always]
    if not every or len(chosen) <= WHOLE_SUITE_SHARE * len(every):
        return []
    print(f"related: {len(chosen)} of {len(every)} test files selected, over half: running the whole suite instead")
    exclude = cfg["tests"].get("related_exclude", [])
    return sorted({f for f in every if not matches(f, exclude)} | set(files))


def run(root: Path, cfg: dict, files: list[str], changed: list[str]) -> int:
    native = cfg["tests"].get("native_related", "")
    exts = set(cfg["code_extensions"])
    changed = [f for f in changed if Path(f).suffix in exts]
    if not changed:
        print("related: no related tests")
        return 0
    always = always_files(root, cfg) & set(files)
    if not native:
        files = whole_suite_over_half(root, cfg, files, always) or files
        always = always_files(root, cfg) & set(files)
    plan = []
    if native:
        plan.append((native, "{changed}", changed, True))
        if always:
            plan.append((cfg["tests"]["runner"], "{files}", sorted(always), False))
    elif files:
        main = [f for f in files if f not in always]
        plan.append((main_runner(cfg, len(main)), "{files}", main, True))
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
    no_tests = set(cfg["tests"].get("no_tests_exit_codes", []))
    elapsed = 0.0
    code = 0
    with log.open("w", encoding="utf-8") as out:
        for step, (template, placeholder, items, timed) in enumerate(plan):
            list_file = log_dir / f"related.files{suffix}-{step}.txt"
            for argv in runner_commands(root, cfg, template, placeholder, items, list_file):
                argv[0] = shutil.which(argv[0]) or argv[0]
                started = time.monotonic()
                returned = subprocess.run(argv, shell=False, cwd=root, stdout=out, stderr=subprocess.STDOUT, check=False).returncode  # noqa: S603
                if timed:
                    elapsed += time.monotonic() - started
                if returned in no_tests:
                    returned = 0
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
    parser.add_argument("--with-always", action="store_true", help="add the tests.always files to the selection")
    parser.add_argument("--args-file", default=None, help="a file with one changed path per line")
    args = parser.parse_args()
    root = repo_root()
    cfg = load(root)
    given = list(args.files)
    if args.args_file:
        given += [line.strip() for line in Path(args.args_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    try:
        changed = given or changed_files(root, resolve_base(root, args.base) if args.base else None)
    except BaseError as e:
        print(f"related: ERROR {e}", file=sys.stderr)
        return 2
    for warning in snapshot_warnings(cfg, changed):
        print(warning)
    files = related(root, cfg, changed, args.with_always)
    if args.run:
        return run(root, cfg, files, changed)
    for f in files:
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())

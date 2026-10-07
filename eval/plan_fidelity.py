"""Plan fidelity (F2, F3): parse spec-kit tasks.md and prd-gate or prd-flow plan.md into tasks with their files."""
import re
import subprocess
from pathlib import Path

SOURCE_DIRS = ("src/",)
FILE_EXT = {"py", "js", "ts", "tsx", "jsx", "md", "json", "yml", "yaml", "toml", "sh", "html",
            "css", "sql", "cfg", "ini", "txt"}
TASK_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+(T\d+)\b(.*)$")
HEAD_RE = re.compile(r"^###\s+(T\d+)\b(.*)$")


def is_test_path(rel):
    parts = rel.split("/")
    name = parts[-1]
    return ("tests" in parts[:-1] or name.startswith("test_") or name.endswith("_test.py")
            or name == "conftest.py")


def is_code_path(rel):
    """Code file: under a source dir, not a test, not a feature CLAUDE.md or other markdown."""
    return (rel.startswith(SOURCE_DIRS) and not is_test_path(rel) and not rel.endswith(".md"))


def clean_token(tok):
    return tok.strip("`'\",;:()<>*").rstrip(".").replace("\\", "/")


def looks_like_file(tok):
    if not tok or "[" in tok or "]" in tok or "://" in tok or "{" in tok:
        return False
    if "/" in tok:
        return True
    ext = tok.rsplit(".", 1)[-1] if "." in tok else ""
    return ext in FILE_EXT and len(tok) > len(ext) + 1


def files_in(text):
    out = []
    for raw in text.split():
        tok = clean_token(raw)
        if looks_like_file(tok) and tok not in out:
            out.append(tok)
    return out


def parse_tasks_md(text):
    """spec-kit: `- [ ] T001 [P] [US1] Description with src/path.py`."""
    tasks = []
    for line in text.splitlines():
        m = TASK_RE.match(line)
        if m:
            tasks.append({"id": m.group(1), "files": files_in(m.group(2)), "source": "tasks.md"})
    return tasks


def parse_plan_md(text):
    """prd-gate and prd-flow: `### T03 · title` blocks, files on the `Owns:` line."""
    tasks, cur = [], None
    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if m:
            cur = {"id": m.group(1), "files": [], "source": "plan.md"}
            tasks.append(cur)
            continue
        if line.startswith("## "):
            cur = None
        o = re.match(r"^\s*Owns:\s*(.*)$", line)
        if o and cur is not None:
            quoted = re.findall(r"`([^`]+)`", o.group(1))
            for part in quoted or o.group(1).split(","):
                tok = clean_token(part.strip())
                if tok and tok not in cur["files"] and " " not in tok:
                    cur["files"].append(tok)
    return tasks


def seed_paths(project, seed):
    if not seed:
        return set()
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", seed], cwd=project,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return set(r.stdout.split("\n")) if r.returncode == 0 else set()


def plan_files(project):
    root = Path(project)
    found = [(p, parse_tasks_md) for p in root.glob("specs/*/tasks.md")]
    found += [(p, parse_plan_md) for p in root.glob("specs/*/plan.md")]
    found += [(p, parse_plan_md) for p in root.glob("changes/**/plan.md")]
    return sorted(found, key=lambda t: str(t[0]))


def load_tasks(project, seed=None):
    """All tasks of the plans created in the run; None when the run has no plan (S size)."""
    root, old = Path(project), seed_paths(project, seed)
    tasks, seen_plan = [], False
    for path, parser in plan_files(project):
        rel = path.relative_to(root).as_posix()
        if rel in old:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        parsed = parser(text)
        if parsed:
            seen_plan = True
            for t in parsed:
                t["plan"] = rel
            tasks += parsed
    return tasks if seen_plan else None


def names(task_file, changed):
    t = task_file.lstrip("./")
    if t.endswith("/"):
        return changed.startswith(t) or ("/" + t) in ("/" + changed)
    return changed == t or changed.endswith("/" + t)


def coverage_and_drift(tasks, changed_files, code_changed, all_changed=None):
    """F2: share of tasks with named files whose files include one changed by a code commit;
    a task naming only docs counts when any commit changed one of them.
    F3: share of changed code files that no task names. None when there is nothing to measure."""
    if tasks is None:
        return None, None
    with_files = [t for t in tasks if t["files"]]
    cov = None
    if with_files:
        def covered(t):
            docs_only = not any(is_code_path(f) or f.startswith("src/") for f in t["files"])
            pool = (all_changed or changed_files) if docs_only else changed_files
            return any(names(f, c) for f in t["files"] for c in pool)
        cov = sum(1 for t in with_files if covered(t)) / len(with_files)
    drift = None
    if code_changed:
        named = [f for t in tasks for f in t["files"]]
        loose = sum(1 for c in code_changed if not any(names(f, c) for f in named))
        drift = loose / len(code_changed)
    return cov, drift

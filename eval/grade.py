"""Grade one finished project against a scenario and print the metrics JSON (EV09)."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

GATE = Path(".claude/skills/prd-gate/scripts/gate.py")
MAX_TEXT = 1_000_000


def git(project, *args):
    r = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def seed_commit(project):
    roots = git(project, "rev-list", "--max-parents=0", "HEAD").split()
    return roots[-1] if roots else None


def project_files(project):
    out = git(project, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted({p for p in out.split("\0") if p and (Path(project) / p).is_file()})


def read_text(path):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    if len(data) > MAX_TEXT or b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="ignore")


def is_test_path(rel):
    parts = rel.split("/")
    name = parts[-1]
    return ("tests" in parts[:-1] or name.startswith("test_") or name.endswith("_test.py")
            or name == "conftest.py")


def run_pytest(workdir, junit, log, args, timeout=900):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(workdir / "src"), str(workdir)]))
    with open(log, "w", encoding="utf-8") as fh:
        try:
            subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            f"--junitxml={junit}", *args], cwd=workdir, env=env,
                           stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 0, 0
    try:
        root = ET.parse(junit).getroot()
    except (OSError, ET.ParseError):
        return 0, 0
    total = bad = 0
    for s in root.iter("testsuite"):
        total += int(s.get("tests", 0))
        bad += int(s.get("failures", 0)) + int(s.get("errors", 0)) + int(s.get("skipped", 0))
    return total - bad, total


def pytest_metrics(project, scenario):
    hidden = scenario / "hidden"
    with tempfile.TemporaryDirectory(prefix="ai-kit-grade-") as tmp:
        tmp = Path(tmp)
        work = tmp / "p"
        shutil.copytree(project, work, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"))
        vp, vt = run_pytest(work, tmp / "visible.xml", tmp / "visible.log",
                            ["--ignore=tests/hidden"])
        hp = ht = None
        if hidden.is_dir():
            shutil.copytree(hidden, work / "tests" / "hidden", dirs_exist_ok=True)
            hp, ht = run_pytest(work, tmp / "hidden.xml", tmp / "hidden.log", ["tests/hidden"])
    return {
        "suite_green": vt > 0 and vp == vt,
        "hidden_passed": hp, "hidden_total": ht,
        "hidden_pass": (hp / ht) if ht else (0.0 if ht == 0 else None),
    }


def gate_ok(project):
    gate = Path(project) / GATE
    if not gate.is_file():
        return False
    try:
        r = subprocess.run([sys.executable, str(gate)], cwd=project, capture_output=True,
                           timeout=300)
    except subprocess.TimeoutExpired:
        return False
    return r.returncode == 0


def prd_text(project):
    chunks = []
    for p in sorted((Path(project) / "docs" / "prd").rglob("*.md")):
        t = read_text(p)
        if t:
            chunks.append(t)
    return "\n".join(chunks)


def prd_ok(project, patterns):
    text = prd_text(project)
    return all(re.search(p, text, re.M) for p in patterns)


def seed_text(project, seed, rel):
    if not seed:
        return ""
    r = subprocess.run(["git", "show", f"{seed}:{rel}"], cwd=project, capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""


def changed_since(project, seed):
    if not seed:
        return set()
    return set(git(project, "diff", "--name-only", seed, "--").split()) | set(
        git(project, "ls-files", "--others", "--exclude-standard").split())


def ids_in_tests(project, files, ids, seed=None):
    if not ids:
        return 1.0
    changed = changed_since(project, seed) if seed else set(files)
    blob = "\n".join(read_text(Path(project) / f) or "" for f in files
                     if is_test_path(f) and f in changed)
    return sum(1 for i in ids if re.search(re.escape(i), blob)) / len(ids)


def docs_first(project, seed):
    if not seed:
        return False
    log = git(project, "log", "--reverse", "--name-only", "--format=%x01%H", f"{seed}..HEAD")
    docs_i = src_i = None
    for i, block in enumerate(b for b in log.split("\x01") if b.strip()):
        names = block.split("\n")[1:]
        if docs_i is None and any(n.startswith("docs/prd/") for n in names):
            docs_i = i
        if src_i is None and any(n.startswith("src/") for n in names):
            src_i = i
    if docs_i is None:
        return False
    return src_i is None or docs_i < src_i


def planned_left(project):
    n = 0
    for p in (Path(project) / "docs" / "prd").rglob("*.md"):
        for line in (read_text(p) or "").splitlines():
            if re.match(r"##\s+Planned\b", line, re.I):
                n += 1
            elif line.lstrip().startswith("|") and re.search(r"\bplanned\b", line, re.I):
                n += 1
    for p in (Path(project) / "docs" / "trd").rglob("*.md"):
        n += sum(1 for line in (read_text(p) or "").splitlines()
                 if re.match(r"##\s+Planned\b", line, re.I))
    return n


def _added(now, before, count):
    return max(0, count(now) - count(before))


def dup_count(project, files, phrases, seed=None):
    def count(text):
        return sum(len(re.findall(ph, text, re.M)) for ph in phrases)

    total = 0
    for f in files:
        if f.startswith(("docs/prd/", "src/", ".claude/prd-gate/state/")) or is_test_path(f):
            continue
        text = read_text(Path(project) / f)
        if text:
            total += _added(text, seed_text(project, seed, f), count)
    return total


def fr_lines(project, files, seed=None):
    def count(text):
        return sum(1 for line in text.splitlines() if re.search(r"FR-\d+", line))

    total = 0
    for f in files:
        if f.startswith("tests/hidden/"):
            continue
        text = read_text(Path(project) / f)
        if text:
            total += _added(text, seed_text(project, seed, f), count)
    return total


def doc_bytes(project, files, seed):
    roots = ("docs/", "specs/", "changes/")
    old = {}
    if seed:
        for line in git(project, "ls-tree", "-r", "-l", seed).splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) == 4 and parts[3].isdigit():
                old[path] = int(parts[3])
    total = 0
    for f in files:
        if f.startswith(roots):
            total += max(0, (Path(project) / f).stat().st_size - old.get(f, 0))
    return total


def load_claude(path):
    if not path:
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if isinstance(data, list):
        data = next((d for d in reversed(data) if isinstance(d, dict)
                     and d.get("type") == "result"), None)
    return data if isinstance(data, dict) else None


def cost_metrics(cj):
    keys = ("cost_usd", "duration_min", "turns", "input_tokens", "output_tokens",
            "cache_read_tokens", "cache_write_tokens", "tokens_total")
    if not cj:
        return {k: None for k in keys}
    usage = cj.get("usage") or {}
    mu = list((cj.get("modelUsage") or {}).values())

    def tok(ukey, mkey):
        if ukey in usage:
            return usage[ukey]
        return sum(m.get(mkey, 0) for m in mu) if mu else None

    vals = [tok("input_tokens", "inputTokens"), tok("output_tokens", "outputTokens"),
            tok("cache_read_input_tokens", "cacheReadInputTokens"),
            tok("cache_creation_input_tokens", "cacheCreationInputTokens")]
    dur = cj.get("duration_ms")
    return {
        "cost_usd": cj.get("total_cost_usd"),
        "duration_min": round(dur / 60000, 3) if isinstance(dur, (int, float)) else None,
        "turns": cj.get("num_turns"),
        "input_tokens": vals[0], "output_tokens": vals[1],
        "cache_read_tokens": vals[2], "cache_write_tokens": vals[3],
        "tokens_total": sum(v for v in vals if v) if any(v is not None for v in vals) else None,
    }


def grade(project, scenario, claude_json=None):
    project, scenario = Path(project).resolve(), Path(scenario).resolve()
    exp = json.loads((scenario / "expected.json").read_text(encoding="utf-8"))
    files = project_files(project)
    seed = seed_commit(project)
    commits = int(git(project, "rev-list", "--count", f"{seed}..HEAD").strip() or 0) if seed else 0
    cj = load_claude(claude_json)
    m = pytest_metrics(project, scenario)
    m.update({
        "gate_ok": gate_ok(project),
        "prd_ok": prd_ok(project, exp.get("prd_patterns", [])),
        "ids_in_tests": ids_in_tests(project, files, exp.get("rule_ids", []), seed),
        "docs_first": docs_first(project, seed) if exp.get("case") == "C5" else None,
        "planned_left": planned_left(project),
        "dup_count": dup_count(project, files, exp.get("dup_phrases", []), seed),
        "fr_lines": fr_lines(project, files, seed),
        **cost_metrics(cj),
        "doc_bytes": doc_bytes(project, files, seed),
        "commits_after_seed": commits,
        "completed": bool(cj) and not cj.get("is_error", False) and commits > 0,
    })
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("scenario")
    ap.add_argument("--claude-json")
    a = ap.parse_args()
    print(json.dumps(grade(a.project, a.scenario, a.claude_json), indent=2))


if __name__ == "__main__":
    main()

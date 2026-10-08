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

import plan_fidelity
import six
from grade_metrics import (blind_metrics, efficiency, review_fix_commits, review_weighted,  # noqa: F401
                          subagent_metrics, task_counts)
from plan_fidelity import is_code_path, is_test_path

SKILL_NAMES = ("prd-flow", "prd-gate")
GATES = [Path(f".claude/skills/{n}/scripts/gate.py") for n in SKILL_NAMES]
STATE_PREFIXES = tuple(f".claude/{n}/state/" for n in SKILL_NAMES)
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
    gate = next((Path(project) / g for g in GATES if (Path(project) / g).is_file()), None)
    if gate is None:
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


def commit_log(project, seed):
    """Commits seed..HEAD oldest first: [{sha, time, subject, files}]."""
    if not seed:
        return []
    log = git(project, "log", "--reverse", "--name-only", "--format=%x01%H%x02%ct%x02%s",
              f"{seed}..HEAD")
    commits = []
    for block in (b for b in log.split("\x01") if b.strip()):
        lines = block.split("\n")
        sha, _, rest = lines[0].partition("\x02")
        ts, _, subject = rest.partition("\x02")
        commits.append({"sha": sha, "time": int(ts) if ts.isdigit() else None, "subject": subject,
                        "files": [n.strip() for n in lines[1:] if n.strip()]})
    return commits


NON_RULE_PREFIXES = {"DEC", "Q"}


def prd_diff_ids(project, seed):
    """Rule IDs in the first cell of PRD table rows added or changed since the seed."""
    ids = []
    for line in git(project, "diff", f"{seed}..HEAD", "--", "docs/prd").splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            m = re.match(r"\+\s*\|\s*([A-Z][A-Z0-9]*-\d+)\s*\|", line)
            if m and m.group(1).split("-")[0] not in NON_RULE_PREFIXES and m.group(1) not in ids:
                ids.append(m.group(1))
    return ids


def traceability(project, files, seed):
    ids = prd_diff_ids(project, seed) if seed else []
    if not ids:
        return None
    changed = changed_since(project, seed)
    blob = "\n".join(read_text(Path(project) / f) or "" for f in files
                     if is_test_path(f) and f in changed)
    return sum(1 for i in ids if re.search(re.escape(i), blob)) / len(ids)


def docs_first(commits):
    docs_i = src_i = None
    for i, c in enumerate(commits):
        if docs_i is None and any(n.startswith("docs/prd/") for n in c["files"]):
            docs_i = i
        if src_i is None and any(is_code_path(n) for n in c["files"]):
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
        code_file = f.startswith("src/") and not f.endswith(".md")
        if f.startswith(("docs/prd/", *STATE_PREFIXES)) or code_file or is_test_path(f):
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


KIT_PREFIXES = (".claude/skills/", "scripts/", ".specify/scripts/")
PROMOTION = re.compile(r"promot|archiv", re.I)
GATE_SKILL = ("prd-flow", "prd-gate")
REQUIRED = {"speckit": [GATE_SKILL, "speckit-specify", "speckit-plan", "speckit-tasks"]}


def conflict_found(project, seed, commits, ids, texts):
    """K-91: a conflict rule ID is named before the first docs/prd commit (assistant text, the state
    folder or changes/), or the PRD diff edits or supersedes that rule. None when the scenario names none."""
    if not ids:
        return None
    pat = re.compile(r"(?<![A-Z0-9-])(?:" + "|".join(re.escape(i) for i in ids) + r")(?!\d)")
    cut = next((i for i, c in enumerate(commits) if any(n.startswith("docs/prd/") for n in c["files"])), None)
    cut_time = commits[cut]["time"] if cut is not None else None
    for line in git(project, "diff", f"{seed}..HEAD", "--", "docs/prd").splitlines():
        if line[:1] in "+-" and not line.startswith(("+++", "---")) and pat.search(line):
            return True
    for item in texts or []:
        t = item.get("t")
        if pat.search(str(item.get("text"))) and (t is None or cut_time is None or t <= cut_time):
            return True
    for prefix in STATE_PREFIXES:
        for path in sorted((Path(project) / prefix).rglob("*")):
            if path.is_file() and (cut_time is None or path.stat().st_mtime <= cut_time):
                if pat.search(read_text(path) or ""):
                    return True
    for c in commits[:cut]:
        for f in c["files"]:
            if f.startswith(STATE_PREFIXES + ("changes/",)):
                r = subprocess.run(["git", "show", f"{c['sha']}:{f}"], cwd=project, capture_output=True)
                if r.returncode == 0 and pat.search(r.stdout.decode("utf-8", "replace")):
                    return True
    return False


def kit_self_fixes(commits):
    return sum(1 for c in commits if any(n.startswith(KIT_PREFIXES) for n in c["files"]))


def code_commits(commits):
    return [c for c in commits if any(is_code_path(n) for n in c["files"])]


def rework_commits(commits):
    seen, first, n = set(), None, 0
    for c in commits:
        code = {f for f in c["files"] if is_code_path(f)}
        if not code:
            continue
        if first is None:
            first = c
        elif code & seen and not PROMOTION.search(c["subject"]):
            n += 1
        seen |= code
    return n


def norm_skill(name):
    return str(name).split(":")[-1].lstrip("/").replace(".", "-").lower()


def protocol_adherence(arm, case, skills):
    if skills is None:
        return None
    sk = str(arm).lower().startswith("sk") or str(arm).lower() in ("speckit", "a")
    need = REQUIRED["speckit"] if (sk and case == "C5") else [GATE_SKILL]
    have = {norm_skill(s) for s in skills}
    return sum(1 for s in need if have & set((s,) if isinstance(s, str) else s)) / len(need)


def impact_writes(transcript):
    """Text written to impact.md or pack.md during the run; a passing close deletes the state folder."""
    found = []
    for line in Path(transcript).read_text(encoding="utf-8", errors="replace").splitlines() if transcript and Path(transcript).exists() else []:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        content = (event.get("message") or {}).get("content") if isinstance(event.get("message"), dict) else None
        for block in content if isinstance(content, list) else []:
            inp = block.get("input") if isinstance(block, dict) and block.get("type") == "tool_use" else None
            if isinstance(inp, dict) and re.search(r"(impact|pack)\.md$", str(inp.get("file_path", ""))):
                found += [str(inp.get(k, "")) for k in ("content", "new_string")]
    return "\n".join(found)


def conflict_recall(project, ids, transcript=None):
    """Share of the expected conflict IDs named in the surveyor's impact or pack; None when none are expected."""
    if not ids:
        return None
    text = "\n".join(read_text(p) or "" for prefix in STATE_PREFIXES
                     for p in sorted((Path(project) / prefix).rglob("impact.md")))
    text += "\n" + impact_writes(transcript)
    return sum(1 for i in ids if re.search(rf"(?<![A-Z0-9-]){re.escape(i)}(?!\d)", text)) / len(ids)


def changed_code_lines(project, seed):
    lines = 0
    for row in git(project, "diff", "--numstat", seed, "--").splitlines() if seed else []:
        add, _, rest = row.partition("\t")
        dele, _, path = rest.partition("\t")
        if is_code_path(path) and add.isdigit() and dele.isdigit():
            lines += int(add) + int(dele)
    return lines


def grade(project, scenario_dir, arm, transcript=None, started_at=None, judge_result=None,
          review_result=None):
    project, scenario = Path(project).resolve(), Path(scenario_dir).resolve()
    exp = json.loads((scenario / "expected.json").read_text(encoding="utf-8"))
    files = project_files(project)
    seed = seed_commit(project)
    commits = commit_log(project, seed)
    eff = efficiency(transcript)
    jr = judge_result or {}
    m = pytest_metrics(project, scenario)
    m["accept"] = m.pop("hidden_pass")
    codes = code_commits(commits)
    changed_in_code_commits = {f for c in codes for f in c["files"]}
    code_changed = sorted({f for c in commits for f in c["files"] if is_code_path(f)})
    tasks = plan_fidelity.load_tasks(project, seed)
    cov, drift = plan_fidelity.coverage_and_drift(
        tasks, changed_in_code_commits, code_changed,
        all_changed={f for c in commits for f in c["files"]})
    start = started_at if started_at is not None else eff["started_at"]
    min_to_code = None
    if codes and codes[0]["time"] is not None and isinstance(start, (int, float)):
        min_to_code = round((codes[0]["time"] - start) / 60, 3)
    docs = [c for c in commits if any(f.startswith("docs/prd/") for f in c["files"])]
    min_to_docs = None
    if docs and docs[0]["time"] is not None and isinstance(start, (int, float)):
        min_to_docs = round((docs[0]["time"] - start) / 60, 3)
    left = planned_left(project)
    dup = dup_count(project, files, exp.get("dup_phrases", []), seed)
    frl = fr_lines(project, files, seed)
    restating = jr.get("restating_files") or []
    m.update({
        "gate_ok": gate_ok(project),
        "completed": (bool(commits) and eff["is_error"] is False) if transcript else None,
        "prd_fidelity": jr.get("prd_fidelity"),
        "plan_coverage": cov, "plan_drift": drift,
        "traceability": traceability(project, files, seed),
        "docs_first": docs_first(commits) if exp.get("case") == "C5" else None,
        "planned_left": left, "promoted": left == 0,
        "dup_count": dup, "fr_lines": frl, "restating_files": len(restating),
        "single_source": dup + frl + len(restating),
        "conflict_found": conflict_found(project, seed, commits, exp.get("conflict_ids") or [],
                                         eff["assistant_texts"]) if seed else None,
        "contradiction_left": jr.get("contradiction_left"),
        "gap_recorded": jr.get("gap_recorded"),
        "tokens_total": eff["tokens_total"], "cost_usd": eff["cost_usd"],
        "wall_min": eff["wall_min"], "turns": eff["turns"], "context_peak": eff["context_peak"],
        "subagents": eff["subagents"], "subagent_token_share": eff["subagent_token_share"],
        "min_to_code": min_to_code, "min_to_docs": min_to_docs, "doc_bytes": doc_bytes(project, files, seed),
        "cost_per_accept": (eff["cost_usd"] / m["hidden_passed"]
                            if eff["cost_usd"] is not None and m["hidden_passed"] else None),
        "tool_errors": eff["tool_errors"],
        "kit_self_fixes": kit_self_fixes(commits), "rework_commits": rework_commits(commits),
        "protocol_adherence": protocol_adherence(arm, exp.get("case"), eff["skills"]),
        "commits_after_seed": len(commits),
        "tokens_main": eff["tokens_main"], "tokens_subagents": eff["tokens_subagents"],
        "tool_calls": eff["tool_calls"], "error_rate": eff["error_rate"],
        "test_runs": eff["test_runs"], "failed_test_runs": eff["failed_test_runs"],
        "review_rounds": eff["review_rounds"],
        "subagent_tokens_median": eff["subagent_tokens_median"],
        "subagent_tool_calls_median": eff["subagent_tool_calls_median"],
        "subagent_errors": eff["subagent_errors"],
        "review_fix_commits": review_fix_commits(commits, eff["subagent_detail"], bool(transcript)),
        **subagent_metrics(eff["subagent_detail"], tasks, cov, eff["wall_min"]),
        **task_counts(tasks, cov, eff["tokens_total"]),
        **{k: eff[k] for k in ("main_min", "agent_min", "cold_starts", "error_kinds",
                               "gate_runs_main", "gate_runs_sub", "cost_main_usd",
                               "cost_subagents_usd", "cache_hit_rate", "output_share",
                               "gate_fail_ratio", "rereads", "docs_dispatched")},
        **blind_metrics(review_result),
    })
    m["conflict_recall"] = conflict_recall(project, exp.get("conflict_ids") or [], transcript)
    m["review_weighted"] = review_weighted(review_result, changed_code_lines(project, seed))
    m["first_pass"] = (bool(m["accept"] == 1.0 and eff["first_pass_clean"])
                       if transcript and eff["first_pass_clean"] is not None else None)
    if exp.get("expected_waves") is not None:
        m["expected_waves"] = exp["expected_waves"]
        m["waves_match"] = (eff["waves"] == exp["expected_waves"]) if eff["waves"] is not None else None
    m["first_pass_rate"] = six.first_pass_rate(m["rework_commits"], m["tasks_done"])
    if not transcript:
        m["subagents_wasted"] = None
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("scenario")
    ap.add_argument("--arm", default="LT")
    ap.add_argument("--transcript", nargs="+")
    ap.add_argument("--started-at", type=float)
    a = ap.parse_args()
    print(json.dumps(grade(a.project, a.scenario, a.arm, a.transcript, a.started_at), indent=2))


if __name__ == "__main__":
    main()

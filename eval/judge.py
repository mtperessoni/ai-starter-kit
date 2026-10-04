"""PRD fidelity judge (F1, F7 part): one `claude -p --model sonnet` call per run. The runner is injectable."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import grade
from plan_fidelity import is_test_path

MAX_DIFF = 60_000
HEAD_LINES = 60
DOC_EXT = (".md", ".html", ".txt")
NO_JUDGE = {"prd_fidelity": None, "facts": None, "restating_files": None, "judge_cost_usd": None}

RUBRIC = """You grade whether a PRD diff states the product facts of a change, strictly.
Verdict per fact, exactly one of:
- stated: the PRD diff (added or changed rows and text) says the fact with the same numbers and boundaries. Example: fact "regular customers are capped at 20%" and the diff adds a row "non-VIP total discount is at most 20% of the subtotal" -> stated.
- missing: the diff does not say it, or says it vaguely or without the number. Example: same fact, diff only says "the cap was lowered" -> missing.
- contradicted: the diff says something incompatible with the fact. Example: same fact, diff says "regular customers are capped at 25%" -> contradicted.
For a fact that says a rule stays unchanged (no change, still documented), the verdict is stated when the diff does not alter or contradict it, contradicted when the diff alters it.
Second task: from the other doc files listed, return those that restate a behavior rule (a number, boundary or condition of product behavior) instead of citing the rule ID in docs/prd. Plans, briefs and TRD files that only cite IDs are not restating.
Answer with one JSON object and nothing else:
{"facts": [{"id": "f1", "verdict": "stated|missing|contradicted"}], "restating_files": ["path"]}
"""


def default_runner(cmd, stdin, cwd):
    exe = shutil.which(cmd[0]) or cmd[0]
    r = subprocess.run([exe, *cmd[1:]], input=stdin, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    return r.returncode, r.stdout


def added_doc_files(project, seed):
    out = grade.git(project, "diff", "--diff-filter=A", "--name-only", seed, "--").split()
    out += grade.git(project, "ls-files", "--others", "--exclude-standard").split()
    files = []
    for f in sorted(set(out)):
        if (f.startswith(("docs/prd/", ".claude/skills/", ".specify/", "tests/hidden/"))
                or is_test_path(f) or not f.endswith(DOC_EXT)):
            continue
        files.append(f)
    return files


def build_prompt(project, scenario_dir, seed):
    project, scenario_dir = Path(project), Path(scenario_dir)
    decisions = (scenario_dir / "decisions.md").read_text(encoding="utf-8")
    exp = json.loads((scenario_dir / "expected.json").read_text(encoding="utf-8"))
    facts = "\n".join(f"{f['id']}: {f['fact']}" for f in exp.get("prd_facts", []))
    diff = grade.git(project, "diff", seed, "--", "docs/prd")[:MAX_DIFF] or "(no change under docs/prd)"
    parts = []
    for rel in added_doc_files(project, seed):
        text = grade.read_text(project / rel) or ""
        head = "\n".join(text.splitlines()[:HEAD_LINES])
        parts.append(f"### {rel}\n{head}")
    others = "\n\n".join(parts) or "(none)"
    return (f"{RUBRIC}\n## Decisions of the change\n{decisions}\n\n## Facts to check\n{facts}\n\n"
            f"## PRD diff\n{diff}\n\n## Other doc files added (first {HEAD_LINES} lines)\n{others}\n")


def parse_verdicts(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def judge(project, scenario_dir, seed, runner=None, model="sonnet"):
    if os.environ.get("EVAL_NO_JUDGE") == "1":
        return dict(NO_JUDGE)
    runner = runner or default_runner
    exp = json.loads((Path(scenario_dir) / "expected.json").read_text(encoding="utf-8"))
    expected = exp.get("prd_facts", [])
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--max-budget-usd", "0.5"]
    try:
        code, out = runner(cmd, build_prompt(project, scenario_dir, seed), str(project))
        envelope = json.loads(out)
    except (OSError, ValueError, subprocess.SubprocessError):
        return dict(NO_JUDGE)
    if not isinstance(envelope, dict):
        return dict(NO_JUDGE)
    cost = envelope.get("total_cost_usd")
    verdicts = parse_verdicts(envelope.get("result") if isinstance(envelope.get("result"), str)
                              else json.dumps(envelope.get("result")))
    if code != 0 or not verdicts:
        return {**NO_JUDGE, "judge_cost_usd": cost}
    by_id = {str(v.get("id")): v.get("verdict") for v in verdicts.get("facts", [])
             if isinstance(v, dict)}
    detail = {f["id"]: by_id.get(f["id"], "missing") for f in expected}
    stated = sum(1 for v in detail.values() if v == "stated")
    bad = sum(1 for v in detail.values() if v == "contradicted")
    fidelity = max(0.0, (stated - bad) / len(expected)) if expected else None
    restating = [f for f in verdicts.get("restating_files", []) if isinstance(f, str)]
    return {"prd_fidelity": fidelity, "facts": detail, "restating_files": restating,
            "judge_cost_usd": cost}

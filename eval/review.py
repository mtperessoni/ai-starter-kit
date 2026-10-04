"""Blind code review (B, X5 and X6): one `claude -p --model sonnet` call per run on the source and
test diff since the seed, with the touched PRD sections as the rules. The runner is injectable."""
import json
import os
import subprocess
from pathlib import Path

import grade
import judge

MAX_PRD = 60_000
MAX_DIFF = 120_000
SEVERITIES = ("critical", "high", "medium", "low")
EXCLUDE = ("docs", "specs", "changes", ".claude", ".specify", "CLAUDE.md", "**/CLAUDE.md")
NO_REVIEW = {"blind_findings": None, "blind_findings_total": None, "blind_bugs": None,
             "blind_approve": None, "blind_detail": None, "review_cost_usd": None}

RUBRIC = """You are a senior code reviewer, strict. Review the code change below (source and tests) against the product rules of the PRD sections given. You do not know how the change was produced; judge only the code.
Report only real problems you can point at in the diff. Do not praise, do not restate the diff.
Severity, exactly one of:
- critical: wrong behavior that loses data or money or breaks a documented rule on the main path. Example: a discount cap of 20% in the PRD is applied after tax, so totals exceed the cap.
- high: wrong behavior on a realistic path, or a documented rule not implemented. Example: the PRD says returns are refused after 30 days and the code accepts any date.
- medium: edge-case bug, missing validation, or a behavior change without a test. Example: an empty cart raises an unhandled exception.
- low: style, naming, small duplication. Example: a magic number repeated in two functions.
Kind, exactly one of: bug, rule_mismatch (code contradicts a PRD rule), test_gap (behavior without a test), maintainability.
Approve only if you would merge the change as is: no critical, no high.
Answer with one JSON object and nothing else:
{"findings": [{"severity": "critical|high|medium|low", "kind": "bug|rule_mismatch|test_gap|maintainability", "file": "path", "summary": "one sentence"}], "approve": true}
"""


def touched_prd(project, seed):
    """Full text of the PRD files changed since the seed; the whole docs/prd tree when none changed."""
    project = Path(project)
    rels = [f for f in grade.git(project, "diff", "--name-only", seed, "--", "docs/prd").split()
            if f.endswith(".md")]
    if not rels:
        rels = sorted(p.relative_to(project).as_posix()
                      for p in (project / "docs" / "prd").rglob("*.md"))
    text = "\n\n".join(f"### {rel}\n{grade.read_text(project / rel) or ''}" for rel in rels)
    return text[:MAX_PRD] or "(no PRD files)"


def code_diff(project, seed):
    spec = [".", *(f":(exclude,glob){p}" if "*" in p else f":(exclude){p}" for p in EXCLUDE)]
    return grade.git(project, "diff", seed, "--", *spec)[:MAX_DIFF] or "(no source or test change)"


def build_prompt(project, seed):
    return (f"{RUBRIC}\n## PRD sections (the rules)\n{touched_prd(project, seed)}\n\n"
            f"## Source and test diff\n{code_diff(project, seed)}\n")


def summarize_findings(data):
    """Counts and flags from the reviewer's JSON; findings that are not well formed are dropped."""
    found = [f for f in data.get("findings", []) if isinstance(f, dict)
             and f.get("severity") in SEVERITIES]
    counts = {s: sum(1 for f in found if f["severity"] == s) for s in SEVERITIES}
    bugs = sum(1 for f in found if f["severity"] in ("critical", "high")
               and f.get("kind") in ("bug", "rule_mismatch"))
    approve = data.get("approve")
    return {"blind_findings": counts, "blind_findings_total": len(found), "blind_bugs": bugs,
            "blind_approve": approve if isinstance(approve, bool) else None, "blind_detail": found}


def review(project, scenario_dir, seed, runner=None, model="sonnet"):
    if os.environ.get("EVAL_NO_REVIEW") == "1" or os.environ.get("EVAL_NO_JUDGE") == "1":
        return dict(NO_REVIEW)
    runner = runner or judge.default_runner
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--max-budget-usd", "2"]
    try:
        code, out = runner(cmd, build_prompt(project, seed), str(project))
        envelope = json.loads(out)
    except (OSError, ValueError, subprocess.SubprocessError):
        return dict(NO_REVIEW)
    if not isinstance(envelope, dict):
        return dict(NO_REVIEW)
    cost = envelope.get("total_cost_usd")
    result = envelope.get("result")
    data = judge.parse_verdicts(result if isinstance(result, str) else json.dumps(result))
    if code != 0 or not data:
        return {**NO_REVIEW, "review_cost_usd": cost}
    return {**summarize_findings(data), "review_cost_usd": cost}

"""Efficiency probe: one fixed coding task, run headless in a throwaway worktree, measured from its own stream.

usage: probe.py --repo <path> --ref <git ref> --label <name> --runs <n> --out <dir> [--model sonnet] [--overlay <dir>]

Each run gets a detached worktree of <repo> at <ref>, a node_modules junction to the repo's own folder, and
optionally an overlay folder copied on top (the kit files under test). The task prompt is task.md beside this
script. One line per run goes to <out>/probe.tsv; the raw stream stays in <out>/<label>-<n>.jsonl.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
INHERITED_PREFIXES = ("CLAUDE_CODE_", "CLAUDE_AGENT_")
INHERITED_NAMES = {"CLAUDECODE", "AI_AGENT", "CLAUDE_PID", "CLAUDE_EFFORT"}
FIELDS = ["label", "run", "ok", "wall_s", "turns", "first_ctx_k", "peak_ctx_k", "tokens_m", "cost_usd",
          "calls", "errors", "read_before_edit", "bash_reads", "lint_calls", "test_runs", "test_fail_streak"]
TEST = re.compile(r"vitest|jest|pytest|gates\.sh (one|related)")
LINT = re.compile(r"eslint|gates\.sh (lint|fix)|ruff|tsc --noEmit")
ALLOWED = ["Read", "Edit", "Write", "Grep", "Glob", "Bash(bash scripts/gates.sh one:*)", "Bash(cat:*)",
           "Bash(head:*)", "Bash(tail:*)", "Bash(sed -n:*)", "Bash(ls:*)", "Bash(grep:*)"]
BASH_READ = re.compile(r"(^|[;&|]\s*)(cat|head|tail|sed -n|less)\s")


def clean_env():
    return {k: v for k, v in os.environ.items()
            if k not in INHERITED_NAMES and not k.startswith(INHERITED_PREFIXES)}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def setup(repo, ref, wt, overlay):
    git(repo, "worktree", "add", "--detach", str(wt), ref)
    src = Path(repo) / "node_modules"
    if src.is_dir():
        subprocess.run(["cmd", "/c", "mklink", "/J", str(wt / "node_modules"), str(src)], capture_output=True, check=True)
    if overlay:
        shutil.copytree(overlay, wt, dirs_exist_ok=True)


def teardown(repo, wt):
    link = wt / "node_modules"
    if link.exists():
        subprocess.run(["cmd", "/c", "rmdir", str(link)], capture_output=True, check=True)
    if not (Path(repo) / "node_modules").is_dir():
        sys.exit("source node_modules disappeared; stopping before any further removal")
    git(repo, "worktree", "remove", "--force", str(wt))


def measure(stream_path):
    m = dict(turns=0, first_ctx=0, peak_ctx=0, tokens=0, cost=0.0, calls=0, errors=0, rbw=0, bash_reads=0,
             lint=0, tests=0, streak=0)
    pend, seen, streak = {}, set(), 0
    for line in stream_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            m["cost"] = e.get("total_cost_usd") or 0.0
        msg = e.get("message") or {}
        if e.get("type") == "assistant" and msg.get("id") not in seen:
            seen.add(msg.get("id"))
            u = msg.get("usage") or {}
            ctx = sum(u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if ctx:
                m["first_ctx"] = m["first_ctx"] or ctx
                m["peak_ctx"] = max(m["peak_ctx"], ctx)
                m["tokens"] += ctx + (u.get("output_tokens") or 0)
                m["turns"] += 1
        for b in msg.get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                m["calls"] += 1
                cmd = (b.get("input") or {}).get("command", "") if b.get("name") in ("Bash", "PowerShell") else ""
                pend[b["id"]] = cmd
                if cmd and BASH_READ.search(cmd):
                    m["bash_reads"] += 1
                if cmd and LINT.search(cmd):
                    m["lint"] += 1
            if b.get("type") == "tool_result":
                cmd = pend.pop(b.get("tool_use_id"), "")
                text = b.get("content") if isinstance(b.get("content"), str) else json.dumps(b.get("content"))
                if b.get("is_error"):
                    m["errors"] += 1
                    if "has not been read yet" in text:
                        m["rbw"] += 1
                if cmd and TEST.search(cmd):
                    m["tests"] += 1
                    failed = b.get("is_error") or re.search(r"\b\d+ failed\b|FAIL\b", text or "")
                    streak = streak + 1 if failed else 0
                    m["streak"] = max(m["streak"], streak)
    return m


def verify(wt):
    test = wt / "src/lib/validators/__tests__/weight.test.ts"
    if not test.is_file():
        return False
    r = subprocess.run(["bash", "scripts/gates.sh", "one", str(test.relative_to(wt)).replace("\\", "/")],
                       cwd=wt, capture_output=True, text=True, timeout=300)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", default="origin/staging")
    ap.add_argument("--label", required=True)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--overlay")
    ap.add_argument("--budget", default="3")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tsv = out / "probe.tsv"
    if not tsv.exists():
        tsv.write_text("\t".join(FIELDS) + "\n", encoding="utf-8")
    prompt = (HERE / "task.md").read_text(encoding="utf-8")
    for n in range(1, a.runs + 1):
        wt = Path(tempfile.gettempdir()) / f"probe-{a.label}-{n}"
        setup(a.repo, a.ref, wt, a.overlay)
        stream = out / f"{a.label}-{n}.jsonl"
        t0 = time.time()
        try:
            with stream.open("w", encoding="utf-8") as fh:
                subprocess.run([shutil.which("claude") or "claude", "-p", "--output-format", "stream-json", "--verbose",
                                "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED,
                                "--model", a.model, "--max-budget-usd", a.budget],
                               input=prompt, stdout=fh, stderr=subprocess.STDOUT, text=True, cwd=wt,
                               env=clean_env(), timeout=1200)
            wall = time.time() - t0
            ok = verify(wt)
        finally:
            m = measure(stream)
            teardown(a.repo, wt)
        row = [a.label, n, int(ok), round(wall), m["turns"], m["first_ctx"] // 1000, m["peak_ctx"] // 1000,
               round(m["tokens"] / 1e6, 2), round(m["cost"], 2), m["calls"], m["errors"], m["rbw"],
               m["bash_reads"], m["lint"], m["tests"], m["streak"]]
        with tsv.open("a", encoding="utf-8") as fh:
            fh.write("\t".join(map(str, row)) + "\n")
        print("\t".join(map(str, row)), flush=True)


if __name__ == "__main__":
    main()

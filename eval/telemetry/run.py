"""Evaluation of the run telemetry (proposals/run-telemetry.md): one clean and one problem session.

python eval/telemetry/run.py [--ref HEAD] [--out eval/results/<stamp>-telemetry] [--only clean|problem] [--dry-run]

Each session builds the small fixture with the kit from --ref, runs `claude -p` with subagents, then
`scripts/retro.py`, and compares the findings with the expectation: the clean session has none; the
problem session has every provoked detector and nothing outside the allowed extras.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable

CLEAN_PROMPT = """You are testing this repository's tooling. Do exactly these steps, nothing else.
1. Use the Agent tool (general-purpose) with this prompt: "In this repository, run the Bash command `bash scripts/gates.sh related src/orders/features/pricing/discount_calculator.py` and reply with its last line."
2. Use the Agent tool (general-purpose) with this prompt: "Read docs/trd/README.md and reply with a 3-line summary."
3. Run the Bash command `bash scripts/gates.sh full`.
4. Answer: done."""

PROBLEM_PROMPT = """You are testing this repository's run telemetry. Do exactly these steps, in order, nothing else. Some commands fail on purpose: do not fix or retry anything beyond what is written.
1. Run in the background (run_in_background) the Bash command `python -c "import sys; sys.stdout.write('y' * 40000000)"`.
2. Use the Agent tool (general-purpose) with this prompt: "Run the Bash command `python -c \\"import time; time.sleep(30)\\"` once and reply done."
3. Use the Agent tool (general-purpose) with this prompt: "Run the Bash command `bash scripts/gates.sh full` once and reply with its last line."
4. Use the Agent tool (general-purpose) with this prompt: "Run the Bash command `python -c \\"print('x' * 300000)\\"` once and reply done."
5. Use the Agent tool (general-purpose) with this prompt: "Run the Bash command `python -c \\"import sys; sys.exit(1)\\"` three times, as three separate Bash calls, ignoring the failure, then reply done."
6. Use the Agent tool (general-purpose) with this prompt: "Run the Bash command `python scripts/run_probe.py --label mem -- python -c \\"b = bytearray(300 * 1024 * 1024); import time; time.sleep(1)\\"` once and reply done."
7. Use the Agent tool (general-purpose) with this prompt: "Run the Bash command `docker build --help` once, then the Bash command `timeout 3 tail -f /dev/null`, ignoring failures, and reply done."
8. Answer: done."""

SESSIONS = {
    "clean": {"prompt": CLEAN_PROMPT, "thresholds": {}, "expect": set(), "allow": set(), "budget": 2},
    "problem": {
        "prompt": PROBLEM_PROMPT,
        "thresholds": {"long_call_s": 20, "memory_mb": 150, "dead_mb": 30},
        "expect": {"long_call", "full_suite_mid_task", "big_output", "loop", "memory",
                   "docker_outside_gates", "unbounded_background", "dead_files"},
        "allow": {"error_rate"},
        "budget": 4,
    },
}


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def build(ref, out):
    done = run([PY, str(ROOT / "eval" / "build.py"), "--ref", ref, "--out", str(out)], ROOT)
    if done.returncode != 0:
        raise SystemExit(f"build failed:\n{done.stdout}{done.stderr}")


def set_thresholds(project, thresholds):
    cfg_path = project / "ai-kit.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg.setdefault("telemetry", {}).update(thresholds)
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    run(["git", "commit", "-qam", "test: telemetry thresholds for the evaluation"], project)


def findings_of(project):
    runs = project / ".ai-kit" / "runs"
    summaries = sorted(runs.glob("*/summary.json"), key=lambda p: p.stat().st_mtime)
    if not summaries:
        return None, None
    data = json.loads(summaries[-1].read_text(encoding="utf-8"))
    found = data.get("findings") or []
    return {f.get("detector") or f.get("id") for f in found}, data


def session(name, spec, ref, out_dir, dry_run):
    project = Path(tempfile.mkdtemp(prefix=f"ai-kit-telemetry-{name}-"))
    shutil.rmtree(project)
    build(ref, project)
    if spec["thresholds"]:
        set_thresholds(project, spec["thresholds"])
    started = time.time()
    if not dry_run:
        exe = shutil.which("claude") or "claude"
        with open(out_dir / f"{name}.claude.json", "w", encoding="utf-8") as so:
            subprocess.run([exe, "-p", "--model", "sonnet", "--output-format", "json",
                            "--dangerously-skip-permissions", "--max-budget-usd", str(spec["budget"])],
                           cwd=project, input=spec["prompt"], stdout=so, stderr=subprocess.DEVNULL,
                           text=True, encoding="utf-8", timeout=1800)
    retro = run([PY, "scripts/retro.py"], project)
    (out_dir / f"{name}.retro.txt").write_text(retro.stdout + retro.stderr, encoding="utf-8")
    found, summary = findings_of(project)
    for f in (project / ".ai-kit" / "runs").glob("*/retro.md"):
        shutil.copyfile(f, out_dir / f"{name}.retro.md")
    for f in (project / ".ai-kit" / "runs").glob("*/summary.json"):
        shutil.copyfile(f, out_dir / f"{name}.summary.json")
    for f in (project / ".ai-kit" / "runs").glob("*/events.jsonl"):
        shutil.copyfile(f, out_dir / f"{name}.events.jsonl")
    found = found or set()
    missing = sorted(spec["expect"] - found)
    unexpected = sorted(found - spec["expect"] - spec["allow"])
    return {"session": name, "project": str(project), "minutes": round((time.time() - started) / 60, 1),
            "findings": sorted(found), "missing": missing, "unexpected": unexpected,
            "ok": summary is not None and not missing and not unexpected,
            "coverage": (summary or {}).get("coverage")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--out")
    ap.add_argument("--only", choices=sorted(SESSIONS))
    ap.add_argument("--dry-run", action="store_true", help="build and run retro without claude")
    a = ap.parse_args(argv)
    out_dir = Path(a.out) if a.out else ROOT / "eval" / "results" / (datetime.now().strftime("%Y-%m-%d") + "-telemetry")
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [session(n, s, a.ref, out_dir, a.dry_run) for n, s in SESSIONS.items() if not a.only or n == a.only]
    (out_dir / "result.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['session']}: {'PASS' if r['ok'] else 'FAIL'} findings={r['findings']} "
              f"missing={r['missing']} unexpected={r['unexpected']} ({r['minutes']} min)")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

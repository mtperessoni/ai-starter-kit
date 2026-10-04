"""Run arm A (main + spec-kit) against arm B (feat/living-truth) per scenario, grade, report (EV08)."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import report  # noqa: E402

ARMS = {"A": {"ref": "main", "spec_kit": True}, "B": {"ref": "feat/living-truth", "spec_kit": False}}


def build_command(budget_usd, claude="claude"):
    return [claude, "-p", "--output-format", "json", "--dangerously-skip-permissions",
            "--max-budget-usd", str(budget_usd)]


def render_prompt(template, request, decisions):
    return template.replace("{request}", request.strip()).replace("{decisions}", decisions.strip())


def build_args(arm, out):
    cfg = ARMS[arm]
    cmd = [sys.executable, str(HERE / "build.py"), "--ref", cfg["ref"], "--out", str(out)]
    return cmd + ["--spec-kit"] if cfg["spec_kit"] else cmd


def kill_tree(proc):
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run_claude(project, prompt, budget, timeout_s, out_json, log):
    exe = shutil.which("claude") or "claude"
    with open(out_json, "w", encoding="utf-8") as so, open(log, "w", encoding="utf-8") as se:
        try:
            proc = subprocess.Popen(build_command(budget, exe), cwd=project, stdin=subprocess.PIPE,
                                    stdout=so, stderr=se, text=True, encoding="utf-8")
        except OSError as e:
            se.write(f"cannot start claude: {e}\n")
            return "crash"
        try:
            proc.communicate(prompt, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            proc.communicate()
            return "timeout"
    return "ok" if proc.returncode == 0 else "crash"


def run_pair(arm, sc, args, projects, results, template):
    name = f"{arm}-{sc}"
    project = projects / name
    scenario = HERE / "scenarios" / sc
    status = "ok"
    t0 = time.time()
    claude_json = results / f"{name}.json"
    b = subprocess.run(build_args(arm, project), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    (results / f"{name}.build.log").write_text(b.stdout + b.stderr, encoding="utf-8")
    if b.returncode != 0:
        status = "build_failed"
    elif args.dry_run:
        status = "dry_run"
        claude_json = None
    else:
        prompt = render_prompt(template, (scenario / "request.md").read_text(encoding="utf-8"),
                               (scenario / "decisions.md").read_text(encoding="utf-8"))
        status = run_claude(project, prompt, args.budget_usd, args.timeout_min * 60, claude_json,
                            results / f"{name}.stderr.log")
    try:
        metrics = grade.grade(project, scenario, claude_json) if status != "build_failed" else {}
    except Exception as e:  # a grading failure must not stop the other pairs
        metrics, status = {"grade_error": str(e)}, "grade_failed"
    metrics["status"] = status
    metrics["wall_min"] = round((time.time() - t0) / 60, 2)
    (results / f"{name}.metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return name, status


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["A", "B"], choices=list(ARMS))
    ap.add_argument("--scenarios", nargs="+", default=["S1", "S2", "S3", "S4"])
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--budget-usd", type=float, default=12)
    ap.add_argument("--timeout-min", type=float, default=45)
    ap.add_argument("--out", help="results folder (default eval/results/<date>)")
    ap.add_argument("--projects", help="folder for the built projects (default in the temp dir)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = Path(args.out) if args.out else HERE / "results" / stamp
    projects = Path(args.projects) if args.projects else \
        Path(tempfile.gettempdir()) / "ai-kit-eval" / stamp
    results.mkdir(parents=True, exist_ok=True)
    projects.mkdir(parents=True, exist_ok=True)
    template = (HERE / "prompt.md").read_text(encoding="utf-8")

    pairs = [(a, s) for s in args.scenarios for a in args.arms]
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        for name, status in pool.map(lambda p: run_pair(*p, args, projects, results, template),
                                     pairs):
            print(f"{name}: {status}", flush=True)
    print(report.write_report(results))


if __name__ == "__main__":
    main()

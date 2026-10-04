"""Run the arms of arms.json over the scenarios, grade each run, report (EV08)."""
import argparse
import json
import os
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
import judge  # noqa: E402
import report  # noqa: E402


def load_config(path=None):
    return json.loads(Path(path or HERE / "arms.json").read_text(encoding="utf-8"))


def plan_pairs(cfg, only=None):
    """arm x scenario x rep, interleaved so a late failure hits both arms alike."""
    pairs = []
    for sc, spec in cfg["scenarios"].items():
        for rep in range(1, int(spec["reps"]) + 1):
            for arm in cfg["arms"]:
                pairs.append({"name": f"{arm}-{sc}-r{rep}", "arm": arm, "scenario": sc, "rep": rep,
                              "budget_usd": spec["budget_usd"]})
    if only:
        known = {p["name"] for p in pairs}
        missing = [n for n in only if n not in known]
        if missing:
            raise SystemExit(f"unknown pair(s): {', '.join(missing)}")
        pairs = [p for p in pairs if p["name"] in only]
    return pairs


def build_command(budget_usd, claude="claude"):
    return [claude, "-p", "--output-format", "stream-json", "--verbose",
            "--dangerously-skip-permissions", "--max-budget-usd", str(budget_usd)]


def render_prompt(template, request, decisions, protocol):
    return (template.replace("{protocol}", protocol.strip()).replace("{request}", request.strip())
            .replace("{decisions}", decisions.strip()))


def build_args(arm_cfg, out):
    cmd = [sys.executable, str(HERE / "build.py"), "--ref", arm_cfg["ref"], "--out", str(out)]
    return cmd + ["--spec-kit"] if arm_cfg["spec_kit"] else cmd


def kill_tree(proc):
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run_claude(project, prompt, budget, timeout_s, out_jsonl, log):
    exe = shutil.which("claude") or "claude"
    with open(out_jsonl, "w", encoding="utf-8") as so, open(log, "w", encoding="utf-8") as se:
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


def run_pair(pair, cfg, args, projects, results, template):
    name, arm, sc = pair["name"], pair["arm"], pair["scenario"]
    arm_cfg = cfg["arms"][arm]
    project, scenario = projects / name, HERE / "scenarios" / sc
    transcript = results / f"{name}.jsonl"
    b = subprocess.run(build_args(arm_cfg, project), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    (results / f"{name}.build.log").write_text(b.stdout + b.stderr, encoding="utf-8")
    started_at = time.time()
    if b.returncode != 0:
        status = "build_failed"
    elif args.dry_run:
        status, transcript = "ok", None
    else:
        prompt = render_prompt(template, (scenario / "request.md").read_text(encoding="utf-8"),
                               (scenario / "decisions.md").read_text(encoding="utf-8"),
                               (HERE / arm_cfg["protocol"]).read_text(encoding="utf-8"))
        status = run_claude(project, prompt, pair["budget_usd"], args.timeout_min * 60, transcript,
                            results / f"{name}.stderr.log")
    wall_min = round((time.time() - started_at) / 60, 3)
    (results / f"{name}.run.json").write_text(json.dumps(
        {"name": name, "arm": arm, "scenario": sc, "rep": pair["rep"], "status": status,
         "started_at": started_at, "runner_wall_min": wall_min}, indent=2), encoding="utf-8")
    metrics = {}
    if status != "build_failed":
        try:
            jr = None
            if not args.dry_run:
                jr = judge.judge(project, scenario, grade.seed_commit(project))
                (results / f"{name}.judge.json").write_text(json.dumps(jr, indent=2), encoding="utf-8")
            metrics = grade.grade(project, scenario, arm=arm, transcript=transcript,
                                  started_at=started_at, judge_result=jr)
        except Exception as e:  # a grading failure must not stop the other pairs
            metrics = {"grade_error": str(e)}
    if metrics.get("wall_min") is None and not args.dry_run:
        metrics["wall_min"] = wall_min  # a killed run has no result event
    metrics = dict(metrics, status=status, runner_wall_min=wall_min)
    (results / f"{name}.metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return name, status


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="arms.json (default eval/arms.json)")
    ap.add_argument("--only", nargs="+", help="rerun only these pairs, e.g. LT-S1-r2")
    ap.add_argument("--parallel", type=int)
    ap.add_argument("--timeout-min", type=float)
    ap.add_argument("--out", help="results folder (default eval/results/<stamp>)")
    ap.add_argument("--projects", help="folder for the built projects (default in the temp dir)")
    ap.add_argument("--dry-run", action="store_true", help="build and grade the seeds; no claude, no judge")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    args.timeout_min = args.timeout_min or cfg["timeout_min"]
    parallel = args.parallel or cfg["parallel"]
    if args.dry_run:
        os.environ["EVAL_NO_JUDGE"] = "1"

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = Path(args.out) if args.out else HERE / "results" / stamp
    projects = Path(args.projects) if args.projects else Path(tempfile.gettempdir()) / "ai-kit-eval" / stamp
    results.mkdir(parents=True, exist_ok=True)
    projects.mkdir(parents=True, exist_ok=True)
    template = (HERE / "prompt.md").read_text(encoding="utf-8")

    pairs = plan_pairs(cfg, args.only)
    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        for name, status in pool.map(lambda p: run_pair(p, cfg, args, projects, results, template), pairs):
            print(f"{name}: {status}", flush=True)
    print(report.write_report(results))


if __name__ == "__main__":
    main()

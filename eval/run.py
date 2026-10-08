"""Run the arms of arms.json over the scenarios, grade each run, report (EV08)."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import judge  # noqa: E402
import report  # noqa: E402
import review  # noqa: E402


QUOTA_HIT = threading.Event()


def load_config(path=None):
    return json.loads(Path(path or HERE / "arms.json").read_text(encoding="utf-8"))


def plan_pairs(cfg, only=None, arms=None):
    """arm x scenario x rep, interleaved so a late failure hits both arms alike."""
    pairs = []
    for sc, spec in cfg["scenarios"].items():
        for rep in range(1, int(spec["reps"]) + 1):
            for arm in cfg["arms"]:
                if arms and arm not in arms:
                    continue
                pairs.append({"name": f"{arm}-{sc}-r{rep}", "arm": arm, "scenario": sc, "rep": rep,
                              "budget_usd": spec["budget_usd"]})
    if only:
        known = {p["name"] for p in pairs}
        missing = [n for n in only if n not in known]
        if missing:
            raise SystemExit(f"unknown pair(s): {', '.join(missing)}")
        pairs = [p for p in pairs if p["name"] in only]
    return pairs


def build_command(budget_usd, claude="claude", model=None, effort=None):
    cmd = [claude, "-p", "--output-format", "stream-json", "--verbose",
           "--dangerously-skip-permissions", "--setting-sources", "project,local"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    cmd += ["--max-budget-usd", str(budget_usd)]
    return cmd


INHERITED_PREFIXES = ("CLAUDE_CODE_", "CLAUDE_AGENT_")
INHERITED_NAMES = {"CLAUDECODE", "AI_AGENT", "CLAUDE_PID", "CLAUDE_EFFORT"}


def operator_config_dir(env=None):
    env = os.environ if env is None else env
    return Path(env.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


AUTH_NAMES = {"CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK",
              "CLAUDE_CODE_USE_VERTEX", "AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "CLOUD_ML_REGION",
              "ANTHROPIC_VERTEX_PROJECT_ID", "ANTHROPIC_BASE_URL"}
AUTH_SOURCES = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK",
                "CLAUDE_CODE_USE_VERTEX")


def hermetic_env(base_env=None, source=None):
    """(temp config folder, env): a fresh CLAUDE_CONFIG_DIR holding only the credentials file, so no
    personal CLAUDE.md, skills, hooks, memory or settings load and auth still works. Auth variables are kept;
    with neither a credentials file nor an auth variable it raises before any run is paid for."""
    full = dict(os.environ if base_env is None else base_env)
    base_env = {k: v for k, v in full.items()
                if k in AUTH_NAMES or not (k.startswith(INHERITED_PREFIXES) or k in INHERITED_NAMES)}
    src = Path(source) if source else operator_config_dir(base_env)
    creds = src / ".credentials.json"
    if not creds.is_file() and not any(base_env.get(k) for k in AUTH_SOURCES):
        raise RuntimeError(f"no credentials: {creds} is missing and none of {', '.join(AUTH_SOURCES)} is set")
    tmp = Path(tempfile.mkdtemp(prefix="ai-kit-claude-"))
    try:
        if creds.is_file():
            shutil.copy2(creds, tmp / ".credentials.json")
    except OSError:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    base_env["CLAUDE_CONFIG_DIR"] = str(tmp)
    return tmp, base_env


def render_prompt(template, request, decisions, protocol):
    return (template.replace("{protocol}", protocol.strip()).replace("{request}", request.strip())
            .replace("{decisions}", decisions.strip()))


def suite_paths(cfg):
    """(fixture, fill file, scenarios folder) of the config; the small suite when absent."""
    fixture = HERE / cfg.get("fixture", "fixture")
    fill = HERE / cfg["fill"] if cfg.get("fill") else fixture / "fill.json"
    return fixture, fill, HERE / cfg.get("scenarios_dir", "scenarios")


def build_args(arm_cfg, out, fixture=None, fill=None, overlay=None):
    cmd = [sys.executable, str(HERE / "build.py"), "--ref", arm_cfg["ref"], "--out", str(out)]
    if fixture:
        cmd += ["--fixture", str(fixture)]
    if fill:
        cmd += ["--fill", str(fill)]
    if overlay and Path(overlay).is_dir():
        cmd += ["--overlay", str(overlay)]
    return cmd + ["--spec-kit"] if arm_cfg["spec_kit"] else cmd


def kill_tree(proc):
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run_claude(project, prompt, budget, timeout_s, out_jsonl, log, model=None, effort=None, env=None):
    exe = shutil.which("claude") or "claude"
    with open(out_jsonl, "w", encoding="utf-8") as so, open(log, "w", encoding="utf-8") as se:
        try:
            proc = subprocess.Popen(build_command(budget, exe, model, effort), cwd=project, env=env,
                                    stdin=subprocess.PIPE, stdout=so, stderr=se, text=True, encoding="utf-8")
        except OSError as e:
            se.write(f"cannot start claude: {e}\n")
            return "crash"
        try:
            proc.communicate(prompt, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            proc.communicate()
            return "timeout"
    return classify(out_jsonl, proc.returncode)


def classify(jsonl, returncode):
    """ok, crash, or rate_limited: a quota stop is infrastructure, not a property of the flow."""
    result = None
    for line in Path(jsonl).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("type") == "result":
            result = e
    text = str((result or {}).get("result", "")).lower()
    if result and (result.get("api_error_status") == 429 or "session limit" in text
                   or "usage limit" in text or "rate limit" in text):
        return "rate_limited"
    if returncode == 0 and result and not result.get("is_error"):
        return "ok"
    return "crash"


def state_slug(project):
    """The change to resume: the newest state folder holding approved-rules.md; when a promotion already
    cleared the state, the newest changes/NNN-<slug> folder; None when neither exists."""
    root = Path(project)
    base = root / ".claude" / "prd-flow" / "state"
    approved = [p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_")
                and (p / "approved-rules.md").is_file()] if base.is_dir() else []
    if approved:
        return max(approved, key=lambda p: (p / "approved-rules.md").stat().st_mtime).name
    changes = root / "changes"
    names = sorted(p.name for p in changes.iterdir()
                   if p.is_dir() and re.match(r"\d+-", p.name)) if changes.is_dir() else []
    return re.sub(r"^\d+-", "", names[-1]) if names else None


def split_budget(budget_usd):
    """(phase 1, phase 2) share of the budget of a two-phase run: 70% and 30%."""
    return round(budget_usd * 0.7, 4), round(budget_usd * 0.3, 4)


def render_phase2(template, slug, decisions):
    return template.replace("{slug}", slug).replace("{decisions}", decisions.strip())


def run_sessions(arm_cfg, cfg, project, prompt, scenario, pair, args, results, name, env):
    """Phase 1, then for a two-phase arm a new session that resumes the change. (status, [transcripts])."""
    model, effort = arm_cfg.get("model", cfg.get("model")), arm_cfg.get("effort", cfg.get("effort"))
    timeout = args.timeout_min * 60
    transcript = results / f"{name}.jsonl"
    two = arm_cfg.get("two_phase")
    if two:
        prompt += "\n\n" + (HERE / "prompt-phase1.md").read_text(encoding="utf-8")
    budget1, budget2 = split_budget(pair["budget_usd"]) if two else (pair["budget_usd"], 0)
    status = run_claude(project, prompt, budget1, timeout, transcript,
                        results / f"{name}.stderr.log", model, effort, env)
    if not two or status != "ok":
        return status, [transcript]
    slug = state_slug(project)
    if slug is None:
        (results / f"{name}.p2.skipped.txt").write_text(
            "phase 2 skipped: no state folder with approved-rules.md and no changes/ folder\n", encoding="utf-8")
        return status, [transcript]
    p2 = results / f"{name}.p2.jsonl"
    prompt2 = render_phase2((HERE / "prompt-phase2.md").read_text(encoding="utf-8"), slug,
                            (scenario / "decisions.md").read_text(encoding="utf-8"))
    status = run_claude(project, prompt2, budget2, timeout, p2, results / f"{name}.p2.stderr.log",
                        arm_cfg.get("phase2_model", "sonnet"), arm_cfg.get("phase2_effort", effort), env)
    return status, [transcript, p2]


def run_pair(pair, cfg, args, projects, results, template):
    name, arm, sc = pair["name"], pair["arm"], pair["scenario"]
    arm_cfg = cfg["arms"][arm]
    fixture, fill, scenarios = suite_paths(cfg)
    project, scenario = projects / name, scenarios / sc
    transcript = results / f"{name}.jsonl"
    if QUOTA_HIT.is_set():
        (results / f"{name}.metrics.json").write_text(json.dumps({"status": "skipped_rate_limit"}),
                                                      encoding="utf-8")
        return name, "skipped_rate_limit"
    b = subprocess.run(build_args(arm_cfg, project, fixture, fill, scenario / "files"), capture_output=True, text=True,
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
        tmp, env = hermetic_env()
        try:
            status, transcripts = run_sessions(arm_cfg, cfg, project, prompt, scenario, pair, args,
                                               results, name, env)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        transcript = transcripts if len(transcripts) > 1 else transcripts[0]
    if status == "rate_limited":
        QUOTA_HIT.set()
    wall_min = round((time.time() - started_at) / 60, 3)
    (results / f"{name}.run.json").write_text(json.dumps(
        {"name": name, "arm": arm, "scenario": sc, "rep": pair["rep"], "status": status,
         "started_at": started_at, "runner_wall_min": wall_min}, indent=2), encoding="utf-8")
    metrics = {}
    if status != "build_failed":
        try:
            jr = rr = None
            if not args.dry_run:
                seed = grade.seed_commit(project)
                jr = judge.judge(project, scenario, seed)
                (results / f"{name}.judge.json").write_text(json.dumps(jr, indent=2), encoding="utf-8")
                rr = review.review(project, scenario, seed)
                (results / f"{name}.review.json").write_text(json.dumps(rr, indent=2), encoding="utf-8")
            metrics = grade.grade(project, scenario, arm=arm, transcript=transcript,
                                  started_at=started_at, judge_result=jr, review_result=rr)
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
    ap.add_argument("--arms", nargs="+", help="run only these arms, e.g. LT SKF")
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
        os.environ["EVAL_NO_REVIEW"] = "1"
    else:
        try:
            shutil.rmtree(hermetic_env()[0], ignore_errors=True)
        except RuntimeError as e:
            raise SystemExit(str(e))

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = Path(args.out) if args.out else HERE / "results" / stamp
    projects = Path(args.projects) if args.projects else Path(tempfile.gettempdir()) / "ai-kit-eval" / stamp
    results.mkdir(parents=True, exist_ok=True)
    projects.mkdir(parents=True, exist_ok=True)
    template = (HERE / "prompt.md").read_text(encoding="utf-8")

    pairs = plan_pairs(cfg, args.only, args.arms)
    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        for name, status in pool.map(lambda p: run_pair(p, cfg, args, projects, results, template), pairs):
            print(f"{name}: {status}", flush=True)
    print(report.write_report(results, base=cfg.get("base", report.BASE), cand=cfg.get("candidate", report.CAND),
                              config=args.config or HERE / "arms.json"))


if __name__ == "__main__":
    main()

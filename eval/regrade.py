"""Recompute every `<name>.metrics.json` of a results folder from the saved transcript, run file and
the built project, then rewrite the report. Saved judge and review JSON are reused unless asked."""
import argparse
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import judge  # noqa: E402
import report  # noqa: E402
import review  # noqa: E402
import run  # noqa: E402

SKIP = report.INFRA | {"crash_no_project"}


def build_stamp(project):
    """Epoch of the `<stamp>` folder run.py builds into (`%Y%m%d-%H%M%S`, local time), else its mtime."""
    try:
        return datetime.strptime(project.parent.name, "%Y%m%d-%H%M%S").timestamp()
    except ValueError:
        return project.stat().st_mtime


def find_project(name, projects=None, started_at=None):
    """`<projects>/<name>`, else the newest `<temp>/ai-kit-eval/*/<name>` built before the run
    started (a later round reuses the same names); None when absent."""
    if projects:
        p = Path(projects) / name
        return p if p.is_dir() else None
    found = [p for p in (Path(tempfile.gettempdir()) / "ai-kit-eval").glob(f"*/{name}") if p.is_dir()]
    if started_at is not None:
        found = [p for p in found if build_stamp(p) <= started_at]
    return max(found, key=build_stamp) if found else None


def load_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def regrade_one(name, results, cfg, projects=None, rejudge=False, rereview=False):
    """Returns the new metrics dict, or None when the run cannot be regraded."""
    results = Path(results)
    meta = load_json(results / f"{name}.run.json")
    jsonl = results / f"{name}.jsonl"
    if not meta or not jsonl.is_file() or meta.get("status") in SKIP:
        return None
    project = find_project(name, projects, meta.get("started_at"))
    if project is None:
        return None
    _, _, scenarios = run.suite_paths(cfg)
    scenario = scenarios / meta["scenario"]
    seed = grade.seed_commit(project)
    jr = load_json(results / f"{name}.judge.json")
    if rejudge:
        jr = judge.judge(project, scenario, seed)
        (results / f"{name}.judge.json").write_text(json.dumps(jr, indent=2), encoding="utf-8")
    rr = load_json(results / f"{name}.review.json")
    if rereview:
        rr = review.review(project, scenario, seed)
        (results / f"{name}.review.json").write_text(json.dumps(rr, indent=2), encoding="utf-8")
    p2 = results / f"{name}.p2.jsonl"
    transcript = [jsonl, p2] if p2.is_file() else jsonl
    metrics = grade.grade(project, scenario, arm=meta["arm"], transcript=transcript,
                          started_at=meta.get("started_at"), judge_result=jr, review_result=rr)
    wall = meta.get("runner_wall_min")
    if metrics.get("wall_min") is None and wall is not None:
        metrics["wall_min"] = wall  # a killed run has no result event
    return dict(metrics, status=meta.get("status"), runner_wall_min=wall)


def regrade(results, config=None, projects=None, rejudge=False, rereview=False):
    cfg = run.load_config(config)
    done, skipped = [], []
    for jsonl in sorted(Path(results).glob("*.jsonl")):
        if jsonl.name.endswith(".p2.jsonl"):
            continue  # phase 2 of a two-phase run, graded with its phase 1
        name = jsonl.stem
        try:
            metrics = regrade_one(name, results, cfg, projects, rejudge, rereview)
        except Exception as e:  # one bad run must not stop the others
            metrics = {"grade_error": str(e)}
        if metrics is None:
            skipped.append(name)
            continue
        (Path(results) / f"{name}.metrics.json").write_text(json.dumps(metrics, indent=2),
                                                            encoding="utf-8")
        done.append(name)
    return done, skipped


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--config", help="arms json (default eval/arms.json)")
    ap.add_argument("--projects", help="folder with the built projects (default: newest in the temp dir)")
    ap.add_argument("--rejudge", action="store_true", help="rerun the PRD judge")
    ap.add_argument("--review", action="store_true", help="rerun the blind review")
    a = ap.parse_args(argv)
    done, skipped = regrade(a.results, a.config, a.projects, a.rejudge, a.review)
    print(f"regraded {len(done)}; skipped {len(skipped)}: {', '.join(skipped) or 'none'}")
    print(report.write_report(a.results, config=a.config or HERE / "arms.json"))


if __name__ == "__main__":
    main()

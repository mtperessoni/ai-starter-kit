"""The six metrics of every round (M1 to M6): fields, derivation from old metrics, aggregation."""
import statistics

KINDS = ("gate_check", "environment", "missing_file", "test_failure", "other")
METRICS = {
    "M1": ("Token consumption", ["tokens_total", "tokens_main", "tokens_subagents", "context_peak",
                                 "cost_usd", "tokens_per_task"]),
    "M2": ("Tasks completed successfully", ["tasks_planned", "tasks_done", "hidden_passed",
                                            "hidden_total", "completed"]),
    "M3": ("Total time", ["wall_min"]),
    "M4": ("Time per run", ["wall_min", "main_min", "agent_min", "cold_starts", "min_to_code",
                            "min_per_task"]),
    "M5": ("Error rate", ["tool_calls", "tool_errors", "error_rate", "gate_runs_main",
                          "gate_runs_sub"] + [f"error_kinds.{k}" for k in KINDS]),
    "M6": ("Implementation versus plan", ["plan_coverage", "plan_drift", "tasks_per_executor",
                                          "review_rounds", "blind_findings_total", "accept"]),
}
ADDITIVE = {"tokens_total", "tokens_main", "tokens_subagents", "cost_usd", "tasks_planned",
            "tasks_done", "hidden_passed", "hidden_total", "completed", "wall_min", "main_min",
            "agent_min", "cold_starts", "tool_calls", "tool_errors", "gate_runs_main",
            "gate_runs_sub", "review_rounds", "blind_findings_total"} | {
    f"error_kinds.{k}" for k in KINDS}
TRANSCRIPT_KEYS = ("main_min", "agent_min", "cold_starts", "error_kinds", "gate_runs_main",
                   "gate_runs_sub")


def _num(v):
    if isinstance(v, bool):
        return float(v)
    return float(v) if isinstance(v, (int, float)) else None


def derive(m, summary=None):
    """Flat per-run dict of every six-metric field; fills what an older metrics.json lacks from the
    transcript summary and from min_per_task and plan_coverage."""
    out = dict(m)
    summary = summary or {}
    for k in TRANSCRIPT_KEYS:
        if out.get(k) is None and summary.get(k) is not None:
            out[k] = summary[k]
    if out.get("tasks_planned") is None:
        wall, per = _num(m.get("wall_min")), _num(m.get("min_per_task"))
        out["tasks_planned"] = round(wall / per) if wall and per else None
    if out.get("tasks_done") is None:
        cov, n = _num(m.get("plan_coverage")), out["tasks_planned"]
        out["tasks_done"] = round(cov * n) if cov is not None and n is not None else None
    if out.get("tokens_per_task") is None:
        tot, done = _num(m.get("tokens_total")), out["tasks_done"]
        out["tokens_per_task"] = tot / done if tot is not None and done else None
    if out.get("main_min") is None and out.get("agent_min") is not None and _num(m.get("wall_min")) is not None:
        out["main_min"] = max(0.0, m["wall_min"] - out["agent_min"])
    if out.get("cold_starts") is None:
        out["cold_starts"] = m.get("subagents")
    kinds = out.get("error_kinds") if isinstance(out.get("error_kinds"), dict) else {}
    for k in KINDS:
        out[f"error_kinds.{k}"] = kinds.get(k) if kinds else None
    return out


def vals(runs, field):
    return [v for v in (_num(r.get(field)) for r in runs) if v is not None]


def aggregate(runs, field):
    """Sum for additive fields, median otherwise; None when no run has the field."""
    v = vals(runs, field)
    if not v:
        return None
    return sum(v) if field in ADDITIVE else statistics.median(v)


def total(runs, field):
    v = vals(runs, field)
    return sum(v) if v and field in ADDITIVE else None


def median(runs, field):
    v = vals(runs, field)
    return statistics.median(v) if v else None

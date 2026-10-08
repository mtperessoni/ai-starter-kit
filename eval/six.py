"""The eight metrics of every round (M1 to M8): fields, derivation from old metrics, aggregation."""
import statistics

KINDS = ("gate_check", "environment", "missing_file", "test_failure", "other")
METRICS = {
    "M1": ("Token consumption", ["cost_per_accept", "tokens_total", "tokens_main", "tokens_subagents", "context_peak",
                                 "start_context", "main_calls", "main_tokens_post_exec", "main_cache_write",
                                 "cost_usd", "cost_main_usd", "cost_subagents_usd", "cache_hit_rate",
                                 "output_share", "tokens_per_task"]),
    "M2": ("Tasks completed successfully", ["tasks_planned", "tasks_done", "hidden_passed",
                                            "hidden_total", "completed"]),
    "M3": ("Total time", ["runner_wall_min", "wall_min"]),
    "M4": ("Time per run", ["runner_wall_min", "wall_min", "main_min", "agent_min", "cold_starts", "min_to_docs",
                            "min_to_code", "min_per_task", "main_only_min", "parallel_factor"]),
    "M5": ("Error rate", ["tool_calls", "tool_errors", "error_rate", "gate_runs_main",
                          "gate_runs_sub", "gate_fail_ratio", "rereads", "rework_actions",
                          "max_reruns_per_step", "ceremony_ratio"] + [f"error_kinds.{k}" for k in KINDS]),
    "M6": ("Implementation versus plan", ["plan_coverage", "plan_drift", "tasks_per_executor",
                                          "first_pass_rate", "first_pass", "review_rounds",
                                          "blind_findings_total", "review_weighted", "accept"]),
    "M7": ("Output quality", ["prd_fidelity", "conflict_found", "contradiction_left",
                              "gap_recorded", "traceability", "single_source", "conflict_recall"]),
    "M8": ("Protocol compliance", ["docs_dispatched", "protocol_adherence", "docs_first", "dispatch_map", "review_coverage",
                                  "main_violations", "chief_violations", "return_compliance", "surveyor_first",
                                  "closed", "inline_residency", "waves"]),
}
SEVERITY_WEIGHTS = {"critical": 8, "high": 4, "medium": 2, "low": 1}
FLOW_KEYS = ("main_calls", "main_tokens_post_exec", "main_cache_write", "cache_busts", "start_context",
             "main_only_min", "main_violations", "inline_residency", "waves", "wave_widths",
             "parallel_factor", "ceremony_ratio", "max_reruns_per_step", "rework_actions",
             "dispatch_map", "review_coverage", "agents_by_role", "first_pass_clean", "main_diff_reads", "main_source_reads",
             "kit_script_reads", "agent_file_edits", "retro_rereads", "cost_by_role", "chief_violations",
             "return_compliance", "surveyor_first", "closed")
LABELS = {"wall_min": "wall_min (active turns only)", "runner_wall_min": "runner_wall_min (run clock)"}
HIGHER, LOWER = "higher", "lower"
DIRECTION = {
    **dict.fromkeys(("tokens_total", "tokens_main", "tokens_subagents", "context_peak", "cost_usd",
                     "cost_main_usd", "cost_subagents_usd", "tokens_per_task", "cost_per_accept", "wall_min",
                     "main_min", "agent_min", "cold_starts", "min_to_docs", "min_to_code",
                     "min_per_task", "runner_wall_min", "tool_errors", "error_rate", "gate_runs_main", "gate_runs_sub",
                     "gate_fail_ratio", "rereads", "plan_drift", "review_rounds",
                     "blind_findings_total", "contradiction_left", "single_source", "start_context",
                     "main_calls", "main_tokens_post_exec", "main_cache_write", "main_only_min",
                     "rework_actions", "max_reruns_per_step", "ceremony_ratio", "review_weighted",
                     "main_violations", "chief_violations", "inline_residency"), LOWER),
    **dict.fromkeys(("cache_hit_rate", "tasks_done", "hidden_passed", "completed", "plan_coverage",
                     "first_pass_rate", "accept", "prd_fidelity", "conflict_found", "gap_recorded",
                     "traceability", "docs_dispatched", "protocol_adherence", "docs_first", "first_pass",
                     "conflict_recall", "dispatch_map", "review_coverage", "parallel_factor", "return_compliance",
                     "closed"), HIGHER),
    **{f"error_kinds.{k}": LOWER for k in KINDS},
}
ADDITIVE = {"tokens_total", "tokens_main", "tokens_subagents", "cost_usd", "tasks_planned",
            "tasks_done", "hidden_passed", "hidden_total", "completed", "wall_min", "main_min",
            "agent_min", "cold_starts", "tool_calls", "tool_errors", "gate_runs_main",
            "gate_runs_sub", "review_rounds", "blind_findings_total", "cost_main_usd",
            "cost_subagents_usd", "rereads", "main_calls", "main_tokens_post_exec", "main_only_min",
            "rework_actions", "main_violations", "chief_violations", "runner_wall_min"} | {
    f"error_kinds.{k}" for k in KINDS}
TRANSCRIPT_KEYS = ("cost_usd", "main_min", "agent_min", "cold_starts", "error_kinds", "gate_runs_main",
                   "gate_runs_sub", "cost_main_usd", "cost_subagents_usd", "cache_hit_rate",
                   "output_share", "gate_fail_ratio", "rereads", "docs_dispatched") + tuple(
    k for k in FLOW_KEYS if k not in ("wave_widths", "agents_by_role", "first_pass_clean", "cost_by_role"))


def _num(v):
    if isinstance(v, bool):
        return float(v)
    return float(v) if isinstance(v, (int, float)) else None


def first_pass_rate(rework_commits, tasks_done):
    r, n = _num(rework_commits), _num(tasks_done)
    return max(0.0, 1 - r / n) if r is not None and n else None


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
    if out.get("first_pass_rate") is None:
        out["first_pass_rate"] = first_pass_rate(m.get("rework_commits"), out["tasks_done"])
    if out.get("first_pass") is None and out.get("first_pass_clean") is not None and _num(m.get("accept")) is not None:
        out["first_pass"] = bool(m["accept"] == 1.0 and out["first_pass_clean"])
    if out.get("cost_per_accept") is None:
        cost, passed = _num(m.get("cost_usd")), _num(m.get("hidden_passed"))
        out["cost_per_accept"] = cost / passed if cost is not None and passed else None
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

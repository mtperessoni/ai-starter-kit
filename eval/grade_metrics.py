"""Metrics of a run computed from its transcript summary, reviewers and plan (split out of grade.py)."""
import re

import six


def efficiency(transcript):
    """Inputs of E1 to E6, R1 and R4 from eval/transcript.py; every key None when unavailable."""
    keys = ("tokens_total", "cost_usd", "wall_min", "turns", "context_peak", "subagents",
            "tool_errors", "subagent_token_share", "skills", "is_error", "started_at",
            "tokens_main", "tokens_subagents", "tool_calls", "error_rate", "test_runs",
            "failed_test_runs", "review_rounds", "subagent_detail", "subagent_tokens_median",
            "subagent_tool_calls_median", "subagent_errors", "assistant_texts",
            "main_min", "agent_min", "cold_starts", "error_kinds", "gate_runs_main",
            "gate_runs_sub", "cost_main_usd", "cost_subagents_usd", "cache_hit_rate",
            "output_share", "gate_fail_ratio", "rereads", "docs_dispatched", *six.FLOW_KEYS)
    empty = {k: None for k in keys}
    if transcript is None:
        return empty
    try:
        import transcript as tr  # lazy: written by another module
        s = (tr.summarize_phases(transcript) if isinstance(transcript, (list, tuple)) and len(transcript) > 1
             else tr.summarize(transcript[0] if isinstance(transcript, (list, tuple)) else transcript))
    except (ImportError, OSError, ValueError):
        return empty
    return {k: s.get(k) for k in keys}


def review_fix_commits(commits, detail, has_transcript):
    """X5: commits made after the first reviewer subagent started, or after the first commit whose
    subject names a review; 0 when the run shows no review, None without a transcript."""
    if not has_transcript:
        return None
    times = [d["started_at"] for d in detail or [] if d.get("review") and d.get("started_at")]
    if times:
        t0 = min(times)
        return sum(1 for c in commits if c["time"] is not None and c["time"] > t0)
    for i, c in enumerate(commits):
        if re.search(r"review", c["subject"], re.I):
            return len(commits) - i - 1
    return 0


def subagent_metrics(detail, tasks, cov, wall_min):
    """X2 and X4: wasted subagents (no file change, not a review), tasks per executor, minutes per task."""
    detail = detail or []
    executors = [d for d in detail if not d.get("review")]
    wasted = sum(1 for d in detail if not d.get("file_changes") and not d.get("review"))
    n = len(tasks) if tasks else 0
    done = round(cov * n) if cov is not None else None
    return {
        "subagents_wasted": wasted if detail else 0,
        "tasks_per_executor": done / len(executors) if executors and done is not None else None,
        "min_per_task": wall_min / n if n and isinstance(wall_min, (int, float)) else None,
    }


def task_counts(tasks, cov, tokens_total):
    """M1 and M2: plan tasks, tasks whose named files a code commit changed, tokens per done task."""
    n = len(tasks) if tasks else 0
    done = round(cov * n) if cov is not None else 0
    per = tokens_total / done if done and isinstance(tokens_total, (int, float)) else None
    return {"tasks_planned": n, "tasks_done": done, "tokens_per_task": per}


def review_weighted(rr, lines):
    """Blind findings weighted Critical 8, High 4, Medium 2, Low 1, per 100 changed lines."""
    counts = (rr or {}).get("blind_findings")
    if not counts or not lines:
        return None
    return sum(w * (counts.get(sev) or 0) for sev, w in six.SEVERITY_WEIGHTS.items()) * 100 / lines


def blind_metrics(rr):
    rr = rr or {}
    counts = rr.get("blind_findings") or {}
    out = {k: rr.get(k) for k in ("blind_findings_total", "blind_bugs", "blind_approve",
                                  "review_cost_usd")}
    for sev in ("critical", "high", "medium", "low"):
        out[f"blind_{sev}"] = counts.get(sev) if counts else None
    return out

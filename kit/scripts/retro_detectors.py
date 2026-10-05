"""Retro detectors (RT12): each takes the parsed run and the thresholds, returns findings only past a threshold."""

import subprocess
import time
from pathlib import Path

DEFAULTS = {
    "long_call_s": 300, "long_test_s": 300, "long_subagent_min": 30, "subagent_tokens": 150000,
    "subagent_tools": 50, "context_peak_tokens": 200000, "big_output_kb": 100, "loop_repeats": 3,
    "edit_repeats": 8, "error_rate": 0.15, "memory_mb": 2048, "disk_drop_mb": 1024, "dead_mb": 500,
    "max_events_mb": 5, "keep_days": 14,
}
EDIT_TOOLS = {"edit", "write", "multiedit"}


def finding(det, value, threshold, seqs=(), agent="main", cmd="", rule="candidate", sev=None, note=""):
    if sev is None:
        sev = "high" if isinstance(value, (int, float)) and threshold and value >= 2 * threshold else "medium"
    return {"id": det, "severity": sev, "value": value, "threshold": threshold,
            "evidence": {"seq": list(seqs), "agent": agent, "cmd": cmd, "note": note}, "rule": rule}


def overlap(a0, a1, waits):
    return sum(max(0.0, min(a1, e) - max(a0, s)) for s, e, _ in waits)


def calls(run):
    """Completed calls with duration (seconds) minus overlapping human waits."""
    out = []
    for e in run["events"]:
        if e.get("ev") not in ("PostToolUse", "PostToolUseFailure") or e.get("ms") is None:
            continue
        dur = e["ms"] / 1000.0
        eff = dur - overlap(e["ts"] - dur, e["ts"], run["waits"])
        out.append({"e": e, "dur": dur, "eff": max(0.0, eff)})
    return out


def _is_wait(e):
    return e.get("cls") == "wait.human" or str(e.get("tool", "")).lower() == "askuserquestion"


def _cmd(e):
    return e.get("cmd", "") or e.get("tool", "")


def long_call(run, th):
    for c in calls(run):
        e = c["e"]
        if _is_wait(e) or str(e.get("tool", "")).lower() == "agent" or str(e.get("cls", "")).startswith("test."):
            continue
        if c["eff"] > th["long_call_s"]:
            yield finding("long_call", round(c["eff"], 1), th["long_call_s"], [e["seq"]], e.get("agent", "main"), _cmd(e))


def slow_test(run, th):
    tests = [c for c in calls(run) if str(c["e"].get("cls", "")).startswith("test.")]
    for c in tests:
        e = c["e"]
        if c["eff"] > th["long_test_s"]:
            yield finding("slow_test", round(c["eff"], 1), th["long_test_s"], [e["seq"]], e.get("agent", "main"), _cmd(e))
    if not tests:
        for p in run["probes"]:
            if (p.get("sec") or 0) > th["long_test_s"]:
                yield finding("slow_test", p["sec"], th["long_test_s"], [], p.get("agent") or "main", p.get("label", ""),
                              note="from resources.jsonl")


def full_suite_mid_task(run, th):
    full = [e for e in run["events"] if e.get("cls") == "test.full" and e.get("ev") == "PreToolUse"]
    if not full:
        full = [e for e in run["events"] if e.get("cls") == "test.full"]
    for e in full:
        if e.get("agent", "main") != "main":
            yield finding("full_suite_mid_task", 1, 0, [e["seq"]], e["agent"], _cmd(e), "TS03", "high")
    main = [e for e in full if e.get("agent", "main") == "main"]
    if len(main) > 1:
        yield finding("full_suite_mid_task", len(main), 1, [e["seq"] for e in main[:-1]], "main",
                      _cmd(main[0]), "TS03", "medium", "more than one before the last")


def long_subagent(run, th):
    for s in run["spans"]:
        if s["kind"] == "subagent" and s["work_s"] > th["long_subagent_min"] * 60:
            yield finding("long_subagent", round(s["work_s"] / 60, 1), th["long_subagent_min"], s["seq"], s["id"], s["atype"])


def heavy_subagent(run, th):
    for s in run["spans"]:
        if s["kind"] != "subagent":
            continue
        for key, lim in (("tokens", th["subagent_tokens"]), ("tools", th["subagent_tools"])):
            if (s.get(key) or 0) > lim:
                yield finding("heavy_subagent", s[key], lim, s["seq"], s["id"], f"{s['atype']} {key}", "SA rules")


def context_peak(run, th):
    for who, peak in run["ctx_peaks"].items():
        if peak > th["context_peak_tokens"]:
            yield finding("context_peak", peak, th["context_peak_tokens"], [], who, "transcript")


def auto_compaction(run, th):
    pre = [e for e in run["events"] if e.get("ev") == "PreCompact" and e.get("trigger") == "auto"]
    if pre:
        yield finding("auto_compaction", len(pre), 0, [e["seq"] for e in pre], "main", "PreCompact auto", sev="medium")


def big_output(run, th):
    for e in run["events"]:
        if (e.get("out_kb") or 0) > th["big_output_kb"]:
            yield finding("big_output", e["out_kb"], th["big_output_kb"], [e["seq"]], e.get("agent", "main"), _cmd(e))


def loop(run, th):
    fails, edits = {}, {}
    for e in run["events"]:
        if e.get("err") and e.get("h"):
            fails.setdefault(e["h"], []).append(e)
        if e.get("ev") == "PostToolUse" and str(e.get("tool", "")).lower() in EDIT_TOOLS:
            for f in e.get("files") or []:
                edits.setdefault(f, []).append(e)
    for h, es in fails.items():
        if len(es) >= th["loop_repeats"]:
            yield finding("loop", len(es), th["loop_repeats"], [x["seq"] for x in es], es[0].get("agent", "main"), _cmd(es[0]),
                          note="same input failing")
    for f, es in edits.items():
        if len(es) >= th["edit_repeats"]:
            yield finding("loop", len(es), th["edit_repeats"], [x["seq"] for x in es], es[0].get("agent", "main"), f,
                          note="same file edited")


def error_rate(run, th):
    cs = calls(run)
    errs = [c["e"] for c in cs if c["e"].get("err")]
    if len(cs) >= 20 and len(errs) / len(cs) > th["error_rate"]:
        yield finding("error_rate", round(len(errs) / len(cs), 3), th["error_rate"], [e["seq"] for e in errs[:10]], "main",
                      f"{len(errs)} of {len(cs)} calls")


def memory(run, th):
    for p in run["probes"]:
        if (p.get("mem_peak_mb") or 0) > th["memory_mb"]:
            yield finding("memory", p["mem_peak_mb"], th["memory_mb"], [], p.get("agent") or "main", p.get("label", ""))


def disk_drop(run, th):
    for p in run["probes"]:
        b, a = p.get("disk_free_gb_before"), p.get("disk_free_gb_after")
        if b is not None and a is not None and (b - a) * 1024 > th["disk_drop_mb"]:
            yield finding("disk_drop", round((b - a) * 1024), th["disk_drop_mb"], [], p.get("agent") or "main", p.get("label", ""))


def docker_outside_gates(run, th):
    for e in run["events"]:
        if e.get("ev") == "PreToolUse" and e.get("cls") in ("docker.build", "docker.run") and "gates.sh" not in (e.get("cmd") or ""):
            yield finding("docker_outside_gates", 1, 0, [e["seq"]], e.get("agent", "main"), _cmd(e), "TS29", "medium")


def unbounded_background(run, th):
    seen = set()
    for e in run["events"]:
        if e.get("cls") == "background.unbounded" and e.get("tuid") not in seen:
            seen.add(e.get("tuid"))
            yield finding("unbounded_background", 1, 0, [e["seq"]], e.get("agent", "main"), _cmd(e), "TS34", "medium")


def killed_call(run, th):
    done = {e.get("tuid") for e in run["events"] if e.get("ev") in ("PostToolUse", "PostToolUseFailure")}
    ends = [e["ts"] for e in run["events"] if e.get("ev") == "SessionEnd"]
    for e in run["events"]:
        if e.get("ev") == "PreToolUse" and e.get("tuid") not in done and ends and max(ends) >= e["ts"]:
            yield finding("killed_call", 1, 0, [e["seq"]], e.get("agent", "main"), _cmd(e), sev="medium",
                          note="PreToolUse with no Post or Failure by session end")


def _size(path: Path, deadline: float):
    total, partial = 0, False
    for p in path.rglob("*"):
        if time.monotonic() > deadline:
            return total, True
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass
    return total, partial


def default_worktrees(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain"],  # noqa: S607
                             capture_output=True, text=True, check=False, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [Path(line[9:]) for line in out.splitlines() if line.startswith("worktree ")]


def dead_files(run, th, temp: Path | None = None, worktrees=default_worktrees, budget=5.0):
    """This run only: task output folders of its sessions, and this project's missing or old worktrees."""
    import tempfile
    temp = temp or Path(tempfile.gettempdir())
    deadline = time.monotonic() + budget
    ids = {s for s in run["session_ids"] if s}
    found, total, partial = [], 0, False
    base = temp / "claude"
    if ids and base.is_dir():
        for tasks in list(base.glob("*/tasks")) + list(base.glob("*/*/tasks")) + list(base.glob("*/*/*/tasks")):
            if not tasks.is_dir():
                continue
            if any(i in part for part in tasks.relative_to(base).parts for i in ids):
                n, part = _size(tasks, deadline)
                total, partial = total + n, partial or part
                found.append(f"{tasks} ({n // 1024} KB)")
    wts = list(worktrees(run["root"]))[1:]
    for w in wts:
        if not w.exists():
            found.append(f"{w} (missing, prunable)")
        elif time.time() - w.stat().st_mtime > th["keep_days"] * 86400:
            n, part = _size(w, deadline)
            total, partial = total + n, partial or part
            found.append(f"{w} (older than {th['keep_days']} days, {n // 1024} KB)")
    if total / 1048576 > th["dead_mb"]:
        yield finding("dead_files", round(total / 1048576, 1), th["dead_mb"], [], "main", "; ".join(found[:5]),
                      note="partial, time budget reached" if partial else "")


DETECTORS = [long_call, slow_test, full_suite_mid_task, long_subagent, heavy_subagent, context_peak, auto_compaction,
             big_output, loop, error_rate, memory, disk_drop, docker_outside_gates, unbounded_background, dead_files,
             killed_call]

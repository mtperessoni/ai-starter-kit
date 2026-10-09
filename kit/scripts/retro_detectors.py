"""Retro detectors (RT12): each takes the parsed run and the thresholds, returns findings only past a threshold."""

import re
import subprocess
import time
from pathlib import Path

DEFAULTS = {
    "long_call_s": 300, "long_test_s": 300, "long_subagent_min": 30, "subagent_tokens": 150000,
    "subagent_tools": 50, "context_peak_tokens": 200000, "big_output_kb": 20, "loop_repeats": 3,
    "edit_repeats": 8, "error_rate": 0.15, "memory_mb": 2048, "disk_drop_mb": 1024, "dead_mb": 500,
    "max_events_mb": 5, "keep_days": 14, "doc_reads": 3,
    "poll_calls": 0, "no_timeout_s": 120,
    "kpi_main_calls": 30, "kpi_inline_reads": 0, "kpi_gate_runs_main": 4, "kpi_parallel_factor_min": 1.5,
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


DOC_DIRS = ("docs/", ".claude/skills/", "changes/")
DOC_TOP = 5


def _doc_path(raw, root):
    p = str(raw or "").replace("\\", "/")
    try:
        r = Path(p)
        if r.is_absolute():
            p = r.resolve().relative_to(Path(root).resolve()).as_posix()
    except (OSError, ValueError):
        pass
    return p if p.startswith(DOC_DIRS) else None


def doc_reads(run, th):
    reads = {}
    for e in run["events"]:
        if e.get("ev") != "PostToolUse" or str(e.get("tool", "")).lower() != "read":
            continue
        p = _doc_path(e.get("cmd"), run["root"])
        if p:
            reads.setdefault(p, []).append(e["seq"])
    ranked = sorted(reads.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:DOC_TOP]
    if not ranked or len(ranked[0][1]) <= th["doc_reads"]:
        return
    parts = []
    for p, seqs in ranked:
        try:
            size = (Path(run["root"]) / p).stat().st_size
        except OSError:
            size = 0
        parts.append(f"{p}: {len(seqs)} reads, rereads {len(seqs) - 1}, {size * len(seqs)} bytes")
    yield finding("doc_reads", len(ranked[0][1]), th["doc_reads"], ranked[0][1], "main", "; ".join(parts), sev="medium")


def _tool_calls(run, tool="bash"):
    """One event per call: the Post when it exists, else the Pre."""
    seen, out = {}, []
    for e in run["events"]:
        if str(e.get("tool", "")).lower() != tool or e.get("ev") not in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
            continue
        key = e.get("tuid") or id(e)
        if key not in seen:
            seen[key] = len(out)
            out.append(e)
        elif e["ev"] != "PreToolUse":
            out[seen[key]] = e
    return out


POLL_CMD = re.compile(r"\b(?:until|while)\b[^\n]*\bsleep\b|(?:^|[;&|(]|\n)\s*sleep\s+\d|\bseq\s+\d")


def poll_calls(run, th):
    polls = [e for e in _tool_calls(run) if POLL_CMD.search(e.get("cmd") or "")]
    if len(polls) > th["poll_calls"]:
        yield finding("poll_calls", len(polls), th["poll_calls"], [e["seq"] for e in polls], polls[0].get("agent", "main"),
                      _cmd(polls[0]), "TS45", "medium", "until, sleep or seq loops wait on a process the harness can notify")


def bg_alive_at_return(run, th):
    alive = [e for e in run["events"] if e.get("ev") == "SubagentStop" and (e.get("bg") or 0) > 0]
    if alive:
        yield finding("bg_alive_at_return", sum(e["bg"] for e in alive), 0, [e["seq"] for e in alive], alive[0].get("agent", "main"),
                      alive[0].get("atype", ""), "TS51", "medium", "background processes alive when an agent handed back")


def no_timeout(run, th):
    slow = [e for e in _tool_calls(run) if e.get("ev") != "PreToolUse" and not e.get("bg") and e.get("timeout") is None
            and (e.get("auto_bg") or (e.get("ms") or 0) > th["no_timeout_s"] * 1000)]
    if slow:
        yield finding("no_timeout", len(slow), 0, [e["seq"] for e in slow], slow[0].get("agent", "main"), _cmd(slow[0]), "TS45",
                      "medium", f"Bash calls over {th['no_timeout_s']} s with no timeout set")


def baseline_in_agent(run, th):
    seen = set()
    for e in _tool_calls(run):
        if e.get("agent", "main") != "main" and re.search(r"gates\.sh\s+baseline|baseline\.py", e.get("cmd") or "") and e.get("tuid") not in seen:
            seen.add(e.get("tuid"))
            yield finding("baseline_in_agent", 1, 0, [e["seq"]], e["agent"], _cmd(e), "TS45", "medium",
                          "the chief records the baseline once, in the background")


GATE_CMD = ("gate.py", "gates.sh")


def kpi_values(run):
    """Delivery KPIs from the events of one run; a value is None when the run cannot answer it."""
    ev = run["events"]
    posts = [e for e in ev if e.get("ev") in ("PostToolUse", "PostToolUseFailure")]
    roles = {}
    starts, spans = {}, []
    for e in ev:
        if e.get("ev") == "SubagentStart":
            roles[e.get("atype") or "unknown"] = roles.get(e.get("atype") or "unknown", 0) + 1
            starts[e.get("agent")] = e["ts"]
        elif e.get("ev") == "SubagentStop" and e.get("agent") in starts:
            spans.append((starts[e["agent"]], e["ts"]))
    first_survey = next((e["ts"] for e in ev if e.get("ev") == "SubagentStart" and str(e.get("atype", "")).endswith("surveyor")), None)
    inline = None
    if first_survey is not None:
        inline = sum(1 for e in posts if e.get("agent", "main") == "main" and str(e.get("tool", "")).lower() == "read"
                     and e["ts"] < first_survey)
    gates = [e for e in ev if e.get("ev") == "PreToolUse" and any(g in (e.get("cmd") or "") for g in GATE_CMD)]
    factor = None
    if len(spans) >= 2:
        window = max(b for _, b in spans) - min(a for a, _ in spans)
        factor = round(sum(b - a for a, b in spans) / window, 2) if window > 0 else None
    return {"main_calls": sum(1 for e in posts if e.get("agent", "main") == "main"), "agents_by_role": roles,
            "inline_reads": inline, "gate_runs_main": sum(1 for e in gates if e.get("agent", "main") == "main"),
            "gate_runs_sub": sum(1 for e in gates if e.get("agent", "main") != "main"), "parallel_factor": factor}


def kpis(run, th):
    k = kpi_values(run)
    roles = ", ".join(f"{r} {n}" for r, n in sorted(k["agents_by_role"].items())) or "none"
    for name in ("main_calls", "inline_reads", "gate_runs_main"):
        if k[name] is not None and k[name] > th[f"kpi_{name}"]:
            yield finding(f"kpi_{name}", k[name], th[f"kpi_{name}"], agent="main", sev="medium", note=f"agents: {roles}")
    pf = k["parallel_factor"]
    if pf is not None and pf < th["kpi_parallel_factor_min"]:
        yield finding("kpi_parallel_factor", pf, th["kpi_parallel_factor_min"], sev="medium", note=f"agents: {roles}")


DETECTORS = [long_call, slow_test, full_suite_mid_task, long_subagent, heavy_subagent, context_peak, auto_compaction,
             big_output, loop, error_rate, memory, disk_drop, docker_outside_gates, unbounded_background, dead_files,
             killed_call, doc_reads, kpis, poll_calls, bg_alive_at_return, no_timeout, baseline_in_agent]

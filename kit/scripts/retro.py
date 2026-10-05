"""Run retrospective (RT09 to RT13): events, resources and transcripts in, spans, summary and retro.md out. Never fails."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retro_detectors as det  # noqa: E402


def jsonl(path: Path) -> list[dict]:
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except ValueError:
                continue
    except OSError:
        pass
    return out


def thresholds(root: Path) -> dict:
    th = dict(det.DEFAULTS)
    try:
        cfg = json.loads((root / "ai-kit.json").read_text(encoding="utf-8")).get("telemetry")
        if isinstance(cfg, dict):
            th.update({k: v for k, v in cfg.items() if k in th and isinstance(v, (int, float))})
    except (OSError, ValueError, AttributeError):
        pass
    return th


def resolve_context(root: Path, given: str | None) -> str:
    if given:
        return given
    if os.environ.get("AI_KIT_CONTEXT"):
        return os.environ["AI_KIT_CONTEXT"]
    try:
        line = (root / ".ai-kit" / "runs" / "current").read_text(encoding="utf-8").splitlines()[0].strip()
        if line:
            return line
    except (OSError, IndexError):
        pass
    try:
        b = subprocess.run(["git", "-C", str(root), "branch", "--show-current"],  # noqa: S607
                           capture_output=True, text=True, check=False, timeout=5).stdout.strip()
        if b:
            return b.replace("/", "-")
    except (OSError, subprocess.SubprocessError):
        pass
    return "default"


def parse_ts(v) -> float | None:
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def read_transcript(path) -> dict | None:
    """Usage per unique requestId (last line wins); None when unreadable."""
    p = Path(str(path))
    if not p.is_file():
        return None
    by_req, n = {}, 0
    for d in jsonl(p):
        u = (d.get("message") or {}).get("usage") if isinstance(d.get("message"), dict) else None
        if d.get("type") != "assistant" or not isinstance(u, dict):
            continue
        n += 1
        by_req[d.get("requestId") or f"line{n}"] = u
    t = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "thinking": 0, "requests": len(by_req), "ctx_peak": 0}
    for u in by_req.values():
        i, c, r = (u.get("input_tokens") or 0), (u.get("cache_creation_input_tokens") or 0), (u.get("cache_read_input_tokens") or 0)
        t["input"] += i
        t["output"] += u.get("output_tokens") or 0
        t["cache_read"] += r
        t["cache_creation"] += c
        t["thinking"] += (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0
        t["ctx_peak"] = max(t["ctx_peak"], i + c + r)
    t["tokens"] = t["input"] + t["output"] + t["cache_creation"]
    return t


def human_waits(events: list[dict]) -> list[tuple[float, float, str]]:
    waits = []
    for i, e in enumerate(events):
        if str(e.get("tool", "")).lower() == "askuserquestion" and e.get("ms") is not None and e.get("ev") != "PreToolUse":
            waits.append((e["ts"] - e["ms"] / 1000.0, e["ts"], e.get("agent", "main")))
        elif e.get("ev") == "Notification":
            for n in events[i + 1:]:
                if n.get("ev") in ("UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure"):
                    waits.append((e["ts"], max(e["ts"], n["ts"]), e.get("agent", "main")))
                    break
    return waits


def build_spans(events, waits, probes, transcripts) -> list[dict]:
    spans = []
    ts = [e["ts"] for e in events]
    wall = (max(ts) - min(ts)) if ts else 0.0
    hw = sum(e - s for s, e, a in waits)
    spans.append({"kind": "main", "id": "main", "wall_s": round(wall, 2), "human_wait_s": round(hw, 2),
                  "work_s": round(max(0.0, wall - hw), 2), "tokens": None, "tools": sum(
                      1 for e in events if e.get("ev") == "PreToolUse" and e.get("agent", "main") == "main"), "seq": []})
    subs = {}
    for e in events:
        aid = e.get("agent")
        if e.get("ev") == "SubagentStart" and aid:
            subs.setdefault(aid, {})["start"] = e["ts"]
            subs[aid]["atype"], subs[aid]["seq"] = e.get("atype", ""), [e["seq"]]
        elif e.get("ev") == "SubagentStop" and aid:
            s = subs.setdefault(aid, {"seq": []})
            s["end"], s["tp"] = e["ts"], e.get("tp")
            s["seq"].append(e["seq"])
            s.setdefault("atype", e.get("atype", ""))
        elif e.get("tool") == "Agent" and isinstance(e.get("sub"), dict) and e["ev"] == "PostToolUse":
            sub = e["sub"]
            s = subs.setdefault(sub.get("id") or e.get("tuid"), {"seq": []})
            s.update({"tokens": sub.get("tokens"), "tools": sub.get("tools"), "status": sub.get("status"), "ms": sub.get("ms")})
            s["seq"].append(e["seq"])
            s.setdefault("atype", "")
            s["call_end"] = e["ts"]
    for aid, s in subs.items():
        w = (s["end"] - s["start"]) if "start" in s and "end" in s else (s.get("ms") or 0) / 1000.0
        sw = sum(b - a for a, b, who in waits if who == aid)
        tr = transcripts.get(aid)
        if s.get("tokens") is None and tr:
            s["tokens"] = tr["tokens"]
        spans.append({"kind": "subagent", "id": aid, "atype": s.get("atype", ""), "wall_s": round(w, 2),
                      "human_wait_s": round(sw, 2), "work_s": round(max(0.0, w - sw), 2), "tokens": s.get("tokens"),
                      "tools": s.get("tools"), "status": s.get("status"), "seq": s["seq"]})
    for p in probes:
        spans.append({"kind": "probe", "id": p.get("label", ""), "wall_s": p.get("sec"), "human_wait_s": 0,
                      "work_s": p.get("sec"), "tokens": None, "mem_peak_mb": p.get("mem_peak_mb"),
                      "tests_collected": p.get("tests_collected"), "tests_failed": p.get("tests_failed"), "seq": []})
    return spans


def load_run(rundir: Path, root: Path) -> dict:
    raw = jsonl(rundir / "events.jsonl")
    events = []
    for i, e in enumerate(raw, 1):
        if isinstance(e.get("ts"), (int, float)) and e.get("ev") != "truncated":
            e["seq"] = i
            events.append(e)
    probes = jsonl(rundir / "resources.jsonl")
    waits = human_waits(events)
    transcripts, tp_total, sids = {}, 0, set()
    for e in events:
        if e.get("sid"):
            sids.add(e["sid"])
        if e.get("tp"):
            tp_total += 1
            stem = Path(str(e["tp"]).replace("\\", "/")).stem
            if len(stem) >= 32:
                sids.add(stem) if e.get("ev") == "SessionStart" else None
            key = "main" if e.get("ev") == "SessionStart" else e.get("agent")
            tr = read_transcript(e["tp"])
            if tr and key:
                transcripts[key] = tr
    run = {"events": events, "probes": probes, "waits": waits, "transcripts": transcripts, "tp_total": tp_total,
           "session_ids": sids, "root": root, "ctx_peaks": {k: t["ctx_peak"] for k, t in transcripts.items()}}
    run["spans"] = build_spans(events, waits, probes, transcripts)
    return run


def coverage(run) -> dict:
    cs = det.calls(run)
    posts = [e for e in run["events"] if e.get("ev") in ("PostToolUse", "PostToolUseFailure")]
    subs = [s for s in run["spans"] if s["kind"] == "subagent"]
    ver = next((e["ver"] for e in run["events"] if e.get("ver")), None)
    return {"events": len(run["events"]), "calls": len(posts), "calls_with_duration_pct": round(100 * len(cs) / len(posts)) if posts else None,
            "subagents": len(subs), "subagents_with_tokens_pct": round(100 * sum(1 for s in subs if s["tokens"] is not None) / len(subs)) if subs else None,
            "main_tokens_covered": "main" in run["transcripts"], "transcripts_read": len(run["transcripts"]),
            "transcripts_named": run["tp_total"], "probes": len(run["probes"]), "version": ver}


def summarize(run, findings, cov) -> dict:
    spans = run["spans"]
    main = spans[0]
    subs = [s for s in spans if s["kind"] == "subagent"]
    top_calls = sorted(det.calls(run), key=lambda c: -c["eff"])[:5]
    mt = run["transcripts"].get("main")
    return {
        "coverage": cov, "findings": findings,
        "totals": {"wall_s": main["wall_s"], "human_wait_s": main["human_wait_s"], "agent_work_s": main["work_s"],
                   "tokens_main": mt["tokens"] if mt else None,
                   "tokens_subagents": sum(s["tokens"] or 0 for s in subs),
                   "context_peak": max(run["ctx_peaks"].values(), default=None)},
        "top_calls": [{"seq": c["e"]["seq"], "s": round(c["eff"], 1), "agent": c["e"].get("agent", "main"), "cmd": det._cmd(c["e"])} for c in top_calls],
        "top_subagents": [{"id": s["id"], "atype": s["atype"], "tokens": s["tokens"], "tools": s["tools"], "work_s": s["work_s"]}
                          for s in sorted(subs, key=lambda s: -(s["tokens"] or 0))[:5]],
        "top_memory": [{"label": p.get("label"), "mem_peak_mb": p.get("mem_peak_mb")}
                       for p in sorted(run["probes"], key=lambda p: -(p.get("mem_peak_mb") or 0))[:5] if p.get("mem_peak_mb")],
    }


def render(ctx: str, s: dict) -> str:
    c, t = s["coverage"], s["totals"]
    pct = lambda v: "n/a" if v is None else f"{v}%"  # noqa: E731
    out = [f"# Retro: {ctx}", "", "## Coverage", "",
           f"- Events: {c['events']}; calls {c['calls']}; with a duration: {pct(c['calls_with_duration_pct'])}",
           f"- Subagents: {c['subagents']}; joined to tokens: {pct(c['subagents_with_tokens_pct'])}; main-thread tokens: "
           + ("covered" if c["main_tokens_covered"] else "not covered (no readable transcript)"),
           f"- Transcripts read: {c['transcripts_read']} of {c['transcripts_named']} named",
           f"- Probes seen: {c['probes']}; Claude Code version: {c['version'] or 'unknown'}", "", "## Findings", ""]
    if not s["findings"]:
        out.append("No finding: the run stayed within every threshold.")
    for f in s["findings"]:
        ev = f["evidence"]
        out.append(f"- **{f['id']}** [{f['severity']}] value {f['value']}, threshold {f['threshold']}; seq {ev['seq'] or '-'}; "
                   f"agent {ev['agent']}; `{ev['cmd']}`; rule {f['rule']}" + (f"; {ev['note']}" if ev["note"] else ""))
    out += ["", "## Time and tokens", "", "| Metric | Value |", "|---|---|"]
    for k, v in t.items():
        out.append(f"| {k} | {'n/a' if v is None else v} |")
    out += ["", "## Top 5", "", "Slowest calls:"]
    out += [f"- seq {x['seq']}, {x['s']} s, {x['agent']}: `{x['cmd']}`" for x in s["top_calls"]] or ["- none"]
    out += ["", "Heaviest subagents:"]
    out += [f"- {x['id']} ({x['atype']}): {x['tokens']} tokens, {x['tools']} tools, {x['work_s']} s" for x in s["top_subagents"]] or ["- none"]
    out += ["", "Memory peaks:"]
    out += [f"- {x['label']}: {x['mem_peak_mb']} MB" for x in s["top_memory"]] or ["- none"]
    return "\n".join(out) + "\n"


def find_change_folder(root: Path, ctx: str) -> Path | None:
    base = root / "changes"
    if base.is_dir() and not ctx.startswith("."):
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name != "archive" and (d.name == ctx or d.name.split("-", 1)[-1] == ctx):
                return d
    return None


def truncate(path: Path, max_mb: float) -> None:
    try:
        if path.stat().st_size > max_mb * 1048576:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            keep = lines[len(lines) // 2:]
            path.write_text(json.dumps({"ev": "truncated", "dropped": len(lines) - len(keep), "ts": time.time()}) + "\n"
                            + "\n".join(keep) + "\n", encoding="utf-8")
    except OSError:
        pass


def prune(root: Path, keep_days: float, now: float | None = None) -> list[str]:
    runs, removed = root / ".ai-kit" / "runs", []
    if not runs.is_dir():
        return removed
    now = now or time.time()
    archived = {d.name.split("-", 1)[-1] for d in (root / "changes" / "archive").iterdir()} | \
               {d.name for d in (root / "changes" / "archive").iterdir()} if (root / "changes" / "archive").is_dir() else set()
    for d in runs.iterdir():
        if not d.is_dir():
            continue
        newest = max((p.stat().st_mtime for p in d.rglob("*") if p.is_file()), default=d.stat().st_mtime)
        if now - newest > keep_days * 86400 or d.name in archived:
            shutil.rmtree(d, ignore_errors=True)
            removed.append(d.name)
    return removed


def analyze(root: Path, ctx: str) -> dict:
    rundir = root / ".ai-kit" / "runs" / ctx
    th = thresholds(root)
    truncate(rundir / "events.jsonl", th["max_events_mb"])
    run = load_run(rundir, root)
    findings = []
    for d in det.DETECTORS:
        try:
            findings += list(d(run, th))
        except Exception as exc:  # noqa: BLE001 - a detector never fails the caller
            print(f"retro: {d.__name__} skipped: {exc}", file=sys.stderr)
    s = summarize(run, findings, coverage(run))
    rundir.mkdir(parents=True, exist_ok=True)
    (rundir / "spans.jsonl").write_text("".join(json.dumps(x) + "\n" for x in run["spans"]), encoding="utf-8")
    (rundir / "summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    md = render(ctx, s)
    (rundir / "retro.md").write_text(md, encoding="utf-8")
    change = find_change_folder(root, ctx)
    if change:
        (change / "retro.md").write_text(md, encoding="utf-8")
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--context")
    ap.add_argument("--root", default=".")
    ap.add_argument("--prune", action="store_true")
    a = ap.parse_args(argv)
    try:
        root = Path(a.root).resolve()
        if a.prune:
            gone = prune(root, thresholds(root)["keep_days"])
            print(f"retro: pruned {len(gone)} run folder(s)" + (": " + ", ".join(gone[:10]) if gone else ""))
            return 0
        ctx = resolve_context(root, a.context)
        s = analyze(root, ctx)
        print(f"retro {ctx}: {len(s['findings'])} finding(s), wall {s['totals']['wall_s']} s, wait {s['totals']['human_wait_s']} s")
        for f in s["findings"][:10]:
            print(f"  {f['id']} [{f['severity']}] {f['value']} > {f['threshold']} seq {f['evidence']['seq'][:5]}")
        print(f"  report: .ai-kit/runs/{ctx}/retro.md")
    except Exception as exc:  # noqa: BLE001
        print(f"retro: failed softly: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

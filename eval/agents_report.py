"""Per-agent table of every run in a results folder: lets an auditor see subagent management (flooding, oversized
prompts and returns, rereads) without reading transcripts. Offline, stdlib only.

Usage: python eval/agents_report.py <results-folder> [--arm ARM] [--scenario S] [--out file.md]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import costs
import protocol

NAME = re.compile(r"^(?P<arm>[^-]+(?:-[A-Z]+)*)-(?P<sc>[A-Z]\d+)-r(?P<n>\d+)$")
PHASE = re.compile(r"\.p\d+$")
SPAWN = {"Agent", "Task"}
LIMITS = {"prompt_chars": 4000, "return_chars": 2000, "files": 25, "rereads": 3, "calls": 50}
FLAG_TEXT = {"prompt_chars": "prompt over 4000 chars", "return_chars": "return over 2000 chars",
             "files": "reads over 25 files", "rereads": "rereads over 3", "calls": "calls over 50"}
COLS = ("role", "model", "calls", "fresh", "cache_read", "cache_write", "output", "cost", "minutes",
        "reads", "files", "rereads", "prompt_chars", "return_chars", "max_context")
SUMMED = ("calls", "fresh", "cache_read", "cache_write", "output", "cost", "minutes", "reads", "rereads",
          "prompt_chars", "return_chars")


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def _events(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict):
            out.append(e)
    return out


def _text_len(b):
    c = b.get("content")
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        return sum(len(x.get("text", "")) for x in c if isinstance(x, dict) and isinstance(x.get("text"), str))
    return 0


def _blocks(e):
    msg = e.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _epoch(ts):
    from datetime import datetime
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _new(role):
    return {"role": role, "model": None, "reads": 0, "paths": set(), "rereads": 0, "prompt_chars": 0,
            "return_chars": 0, "t0": None, "t1": None, "minutes": 0.0}


def _agent_rows(paths):
    agents = {"main": _new("main")}
    msgs, reported = {}, {}
    main_minutes = 0.0
    for path in paths:
        seen = {}
        for e in _events(path):
            kind, parent = e.get("type"), e.get("parent_tool_use_id")
            key = parent if parent in agents else "main" if parent is None else None
            ts = _epoch(e["timestamp"]) if e.get("timestamp") else None
            if parent and parent in agents and ts is not None:
                a = agents[parent]
                a["t0"] = ts if a["t0"] is None else min(a["t0"], ts)
                a["t1"] = ts if a["t1"] is None else max(a["t1"], ts)
            if kind == "result":
                main_minutes += _num(e.get("duration_ms")) / 60000
                agents["main"]["return_chars"] = max(agents["main"]["return_chars"], len(str(e.get("result") or "")))
                for m, v in (e.get("modelUsage") or {}).items():
                    if isinstance(v, dict):
                        reported.setdefault(m, {"costUSD": 0.0})["costUSD"] += _num(v.get("costUSD"))
            elif kind == "assistant" and key:
                msg = e.get("message") if isinstance(e.get("message"), dict) else {}
                usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
                mid = msg.get("id") or f"anon-{len(msgs)}"
                msgs[mid] = (key, msg.get("model"), usage)
                if msg.get("model"):
                    agents[key]["model"] = msg["model"]
                for b in _blocks(e):
                    if b.get("type") != "tool_use":
                        continue
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    if b.get("name") == "Read" and isinstance(inp.get("file_path"), str):
                        a, s = agents[key], seen.setdefault(key, set())
                        a["reads"] += 1
                        a["rereads"] += inp["file_path"] in s
                        s.add(inp["file_path"])
                        a["paths"].add(inp["file_path"])
                    if b.get("name") in SPAWN and key == "main":
                        a = _new(protocol.role_of(inp))
                        a["prompt_chars"] = len(str(inp.get("prompt", "")))
                        agents[b.get("id")] = a
            elif kind == "user":
                for b in _blocks(e):
                    if b.get("type") == "tool_result" and b.get("tool_use_id") in agents:
                        a = agents[b["tool_use_id"]]
                        a["return_chars"] = max(a["return_chars"], _text_len(b))
    spent = costs.role_costs([(k, m, u) for k, m, u in msgs.values()], reported)
    rows = []
    for key, a in agents.items():
        mine = [u for k, _, u in msgs.values() if k == key]
        if key != "main" and not mine:
            continue
        ctx = max([sum(_num(u.get(x)) for x in ("input_tokens", "cache_read_input_tokens",
                                                 "cache_creation_input_tokens")) for u in mine] or [0])
        minutes = main_minutes if key == "main" else ((a["t1"] - a["t0"]) / 60 if a["t0"] is not None else 0.0)
        row = {"role": a["role"], "agent": key, "model": a["model"] or "-", "calls": len(mine),
               "fresh": sum(_num(u.get("input_tokens")) for u in mine),
               "cache_read": sum(_num(u.get("cache_read_input_tokens")) for u in mine),
               "cache_write": sum(_num(u.get("cache_creation_input_tokens")) for u in mine),
               "output": sum(_num(u.get("output_tokens")) for u in mine), "cost": spent.get(key, 0.0),
               "minutes": minutes, "reads": a["reads"], "files": len(a["paths"]), "rereads": a["rereads"],
               "prompt_chars": a["prompt_chars"], "return_chars": a["return_chars"], "max_context": ctx}
        row["flags"] = [FLAG_TEXT[k] for k, limit in LIMITS.items() if row[k] > limit]
        rows.append(row)
    return rows


def _logs(folder, stem):
    base = Path(folder) / f"{stem}.jsonl"
    return [base] + sorted(Path(folder).glob(f"{stem}.p[2-9].jsonl"))


def report_runs(folder, arm=None, scenario=None):
    """[{name, rows, totals, flags}] per run of the folder, filtered by arm and scenario."""
    runs = []
    for f in sorted(Path(folder).glob("*.jsonl")):
        stem = f.name[:-len(".jsonl")]
        m = NAME.match(stem)
        if PHASE.search(stem) or not m or (arm and m["arm"] != arm) or (scenario and m["sc"] != scenario):
            continue
        rows = _agent_rows(_logs(folder, stem))
        totals = {k: sum(r[k] for r in rows) for k in SUMMED}
        totals["max_context"] = max((r["max_context"] for r in rows), default=0)
        flags = [f"{r['role']} ({r['agent'][-6:]}): {t}" for r in rows for t in r["flags"]]
        runs.append({"name": stem, "rows": rows, "totals": totals, "flags": flags})
    return runs


def _cell(col, v):
    if col == "cost":
        return f"{v:.2f}"
    if col == "minutes":
        return f"{v:.1f}"
    return f"{v:,}" if isinstance(v, int) else str(v)


def render(runs):
    out = ["# Agents report", ""]
    for run in runs:
        out += [f"## {run['name']}", "", "| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
        for r in run["rows"]:
            out.append("| " + " | ".join(_cell(c, r[c]) for c in COLS) + " |")
        t = run["totals"]
        out.append("| **total** | | " + " | ".join(
            _cell(c, t[c]) if c in t else "" for c in COLS[2:]) + " |")
        out += ["", "Flags: " + ("; ".join(run["flags"]) if run["flags"] else "none"), ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder")
    ap.add_argument("--arm")
    ap.add_argument("--scenario")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    text = render(report_runs(a.folder, a.arm, a.scenario))
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()

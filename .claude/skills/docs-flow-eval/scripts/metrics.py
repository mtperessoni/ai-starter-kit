"""Efficiency of one arm run from its subagent transcripts.

Usage: python metrics.py <session dir> <label>=<agentId>[,<agentId>...] ...
Prints one row per label: wall, active, turns, output and input tokens, tool calls, gate runs and failures, test runs, edits by kind.
"""
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

GATE = re.compile(r"gate\.py|gate_lite\.py|gates\.sh (docs|close)")
TEST = re.compile(r"vitest|gates\.sh (one|red|related|verify)")
DOC = re.compile(r"docs/(prd|trd|adr)|CHANGELOG|/changes/|\.claude/prd-flow/state|CLAUDE\.md|INDEX\.md", re.I)
TESTF = re.compile(r"__tests__|\.test\.")


def ts(e):
    return dt.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).timestamp()


def one(path: Path) -> collections.Counter:
    c = collections.Counter()
    ents = [json.loads(l) for l in path.read_text(encoding="utf-8", errors="ignore").splitlines() if l.startswith("{")]
    ents = [e for e in ents if e.get("timestamp")]
    t = [ts(e) for e in ents]
    c["wall_s"] += t[-1] - t[0]
    c["active_s"] += sum(min(b - a, 900) for a, b in zip(t, t[1:]))
    seen, pend = set(), {}
    for e in ents:
        m = e.get("message") or {}
        if e.get("type") == "assistant" and m.get("id") not in seen:
            seen.add(m.get("id"))
            u = m.get("usage") or {}
            c["turns"] += 1
            c["out_tok"] += u.get("output_tokens", 0)
            c["in_tok"] += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                c["tool_calls"] += 1
                i = b.get("input") or {}
                if b["name"] in ("Bash", "PowerShell"):
                    cmd = i.get("command", "")
                    if GATE.search(cmd):
                        c["gate_runs"] += 1
                        pend[b["id"]] = "gate"
                    elif TEST.search(cmd):
                        c["test_runs"] += 1
                if b["name"] in ("Edit", "Write"):
                    p = i.get("file_path", "").replace("\\", "/")
                    c["edits_doc" if DOC.search(p) else "edits_test" if TESTF.search(p) else "edits_code"] += 1
                if b["name"] == "Read":
                    c["reads"] += 1
            if b.get("type") == "tool_result" and pend.pop(b.get("tool_use_id"), None):
                if re.search(r"\bERROR\b|\bL[1-5] |FAILED|exit code [1-9]|Exit code [1-9]", json.dumps(b.get("content"))):
                    c["gate_fail"] += 1
    return c


def main() -> None:
    root = Path(sys.argv[1]) / "subagents"
    cols = ["agents", "wall_s", "active_s", "turns", "out_tok", "in_tok", "tool_calls", "reads", "gate_runs", "gate_fail", "test_runs", "edits_doc", "edits_code", "edits_test"]
    print("| arm | " + " | ".join(cols) + " |")
    print("|---" * (len(cols) + 1) + "|")
    for arg in sys.argv[2:]:
        label, ids = arg.split("=")
        total = collections.Counter()
        for aid in ids.split(","):
            total.update(one(root / f"agent-{aid}.jsonl"))
            total["agents"] += 1
        vals = [f"{total[k] / 60:.1f} min" if k.endswith("_s") else f"{total[k] / 1000:.0f}k" if k.endswith("_tok") else str(total[k]) for k in cols]
        print(f"| {label} | " + " | ".join(vals) + " |")


if __name__ == "__main__":
    main()

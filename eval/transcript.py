"""Summarize a `claude -p --output-format stream-json --verbose` transcript (E1 to E7 inputs, R1, R4)."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import costs
import protocol

USAGE_KEYS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
MODEL_KEYS = {"input_tokens": "inputTokens", "output_tokens": "outputTokens",
              "cache_read_tokens": "cacheReadInputTokens", "cache_write_tokens": "cacheCreationInputTokens"}
COMMAND_RE = re.compile(r"<command-name>\s*/?([\w:.-]+)\s*</command-name>")
SPAWN_TOOLS = {"Agent", "Task"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
TEST_CMD_RE = re.compile(r"\b(pytest|unittest)\b|gates\.sh")
REVIEW_ROUND_RE = re.compile(r"review:\s*(\d+)\s*/\s*5", re.I)
FAIL_COUNT_RE = re.compile(r"(\d+)\s+(?:failed|failures?|errors?)\b", re.I)
GATE_ERR_RE = re.compile(r"ERROR (?:Q\d|G\d+|P\d)")
ENV_ERR_RE = re.compile(r"python: not found|python3?: command not found|No such file or directory: ?'python|"
                        r"can't open file|command not found|EISDIR|unexpected EOF", re.I)
MISSING_RE = re.compile(r"File does not exist")
TEST_ERR_RE = re.compile(r"FAILED|AssertionError|Traceback")
ERROR_KINDS = ("gate_check", "environment", "missing_file", "test_failure", "other")
DOCS_AGENT_RE = re.compile(r"writer|planner", re.I)
UNITTEST_FAIL_RE = re.compile(r"\bFAILED \((?:failures|errors)=", re.I)


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def _events(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict):
            yield e


def _blocks(e):
    msg = e.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _epoch(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _total(usage):
    return sum(_num(usage.get(k)) for k in USAGE_KEYS)


def _result_text(b):
    c = b.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict)
                         and isinstance(x.get("text"), str))
    return ""


def _test_failed(b):
    text = _result_text(b)
    return (b.get("is_error") is True or UNITTEST_FAIL_RE.search(text) is not None
            or any(int(n) > 0 for n in FAIL_COUNT_RE.findall(text)))


def _error_kind(text, is_error):
    if GATE_ERR_RE.search(text):
        return "gate_check"
    if not is_error:
        return None
    for kind, rx in (("environment", ENV_ERR_RE), ("missing_file", MISSING_RE),
                     ("test_failure", TEST_ERR_RE)):
        if rx.search(text):
            return kind
    return "other"


def _median(vals):
    vals = sorted(vals)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def _is_review(inp):
    return "review" in f"{inp.get('subagent_type', '')} {inp.get('description', '')}".lower()


def _usage_ratios(model_usage, main_model):
    """(cost_main, cost_subagents, cache_hit_rate, output_share) from the result's modelUsage; None when absent."""
    if not isinstance(model_usage, dict) or not model_usage:
        return None, None, None, None
    rows = {k: v for k, v in model_usage.items() if isinstance(v, dict)}
    cost_main = cost_sub = None
    if main_model in rows:
        cost_main = sum(_num(v.get("costUSD")) for k, v in rows.items() if k == main_model)
        cost_sub = sum(_num(v.get("costUSD")) for k, v in rows.items() if k != main_model)
    tok = {key: sum(_num(v.get(key)) for v in rows.values()) for key in MODEL_KEYS.values()}
    total = sum(tok.values())
    prompt = tok["inputTokens"] + tok["cacheReadInputTokens"] + tok["cacheCreationInputTokens"]
    return (cost_main, cost_sub, tok["cacheReadInputTokens"] / prompt if prompt else None,
            tok["outputTokens"] / total if total else None)


def summarize(path, carry=None):
    msgs = {}  # assistant message id -> (usage, is_subagent); one id spans several events
    meta, role_by_id, dur_total = {}, {}, None  # message id -> (model, parent); Agent call id -> role
    tool_errors, subagents, skills, started, result = 0, 0, set(), None, None
    tool_calls, test_ids, test_runs, failed_tests, rounds = 0, set(), 0, 0, 0
    details, awaiting_ts = {}, []  # Agent tool_use id -> detail
    sub_msgs_by = {}  # parent id -> {message id: usage}
    spans = {}  # parent id -> [first, last] event time
    kinds, gate_main, gate_sub = dict.fromkeys(ERROR_KINDS, 0), 0, 0
    texts = []  # main-thread assistant text blocks with their event time
    main_model, gate_ids, gate_failed, reads, rereads, docs_dispatched = None, set(), set(), {}, 0, False
    events = list(_events(path))
    for n, e in enumerate(events):
        kind = e.get("type")
        if e.get("timestamp"):
            ts = _epoch(e["timestamp"])
            if started is None:
                started = ts
            if e.get("parent_tool_use_id") and ts is not None:
                sp = spans.setdefault(e["parent_tool_use_id"], [ts, ts])
                sp[0], sp[1] = min(sp[0], ts), max(sp[1], ts)
            for d in awaiting_ts:
                d["started_at"] = ts
            awaiting_ts = []
        parent = e.get("parent_tool_use_id")
        if kind == "result":
            result = e
            if isinstance(e.get("duration_ms"), (int, float)):
                dur_total = (dur_total or 0) + e["duration_ms"]
        elif kind == "system" and e.get("subtype") == "init" and isinstance(e.get("model"), str):
            main_model = e["model"]
        elif kind == "assistant":
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            mid = msg.get("id") or f"anon-{n}"
            msgs[mid] = (usage, parent is not None)
            meta[mid] = (msg.get("model"), parent)
            if parent is not None:
                sub_msgs_by.setdefault(parent, {})[mid] = usage
            for b in _blocks(e):
                if b.get("type") == "text" and parent is None:
                    texts.append({"t": _epoch(e["timestamp"]) if e.get("timestamp") else None,
                                  "text": str(b.get("text"))})
                    for r in REVIEW_ROUND_RE.findall(str(b.get("text"))):
                        rounds = max(rounds, int(r))
                if b.get("type") != "tool_use":
                    continue
                tool_calls += 1
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                if b.get("name") == "Read" and isinstance(inp.get("file_path"), str):
                    seen = reads.setdefault(parent, set())
                    rereads += inp["file_path"] in seen
                    seen.add(inp["file_path"])
                if b.get("name") in SPAWN_TOOLS and DOCS_AGENT_RE.search(
                        f"{inp.get('description', '')} {inp.get('prompt', '')}"):
                    docs_dispatched = True
                if "gate.py" in json.dumps(inp):
                    gate_ids.add(b.get("id"))
                    if parent is None:
                        gate_main += 1
                    else:
                        gate_sub += 1
                if parent is not None and parent in details:
                    details[parent]["tool_calls"] += 1
                    if b.get("name") in EDIT_TOOLS:
                        details[parent]["file_changes"] += 1
                if b.get("name") in SPAWN_TOOLS:
                    subagents += 1
                    d = {"id": b.get("id"), "type": inp.get("subagent_type"),
                         "description": inp.get("description"), "tokens": 0, "tool_calls": 0,
                         "tool_errors": 0, "return_lines": 0, "is_error": False,
                         "started_at": None, "file_changes": 0, "review": _is_review(inp)}
                    details[b.get("id")] = d
                    role_by_id[b.get("id")] = protocol.role_of(inp)
                    awaiting_ts.append(d)
                elif b.get("name") == "Bash" and TEST_CMD_RE.search(str(inp.get("command", ""))):
                    test_runs += 1
                    test_ids.add(b.get("id"))
                if b.get("name") == "Skill":
                    name = inp.get("skill") or inp.get("name")
                    if name:
                        skills.add(str(name).lstrip("/"))
        elif kind == "user":
            for b in _blocks(e):
                if b.get("type") == "tool_result":
                    tid = b.get("tool_use_id")
                    if tid in gate_ids and (b.get("is_error") is True
                                            or "ERROR " in _result_text(b)):
                        gate_failed.add(tid)
                    kind_err = _error_kind(_result_text(b), b.get("is_error") is True)
                    if kind_err:
                        kinds[kind_err] += 1
                    if b.get("is_error") is True:
                        tool_errors += 1
                        if parent in details:
                            details[parent]["tool_errors"] += 1
                    if tid in test_ids and _test_failed(b):
                        failed_tests += 1
                    if tid in details:
                        text = _result_text(b)
                        details[tid]["return_lines"] = len(text.splitlines()) if text else 0
                        details[tid]["is_error"] = b.get("is_error") is True
                elif b.get("type") == "text" and isinstance(b.get("text"), str):
                    skills.update(COMMAND_RE.findall(b["text"]))

    sums = {k: sum(_num(u.get(k)) for u, _ in msgs.values()) for k in USAGE_KEYS}
    tokens = dict(zip(MODEL_KEYS, (sums[k] for k in USAGE_KEYS)))
    r = result or {}
    model_usage = r.get("modelUsage")
    if isinstance(model_usage, dict) and model_usage:
        tokens = {k: sum(_num(m.get(v)) for m in model_usage.values() if isinstance(m, dict))
                  for k, v in MODEL_KEYS.items()}
    cost_main, cost_sub, cache_hit, out_share = _usage_ratios(model_usage, main_model)
    priced = [("main" if meta[m][1] is None else role_by_id.get(meta[m][1], "other"), meta[m][0], u)
              for m, (u, _) in msgs.items() if meta[m][0]]
    by_role = costs.role_costs(priced, model_usage) if priced else {}
    if by_role:
        cost_main = by_role.get("main", 0.0)
        cost_sub = sum(v for k, v in by_role.items() if k != "main")
    all_msgs = sum(_total(u) for u, _ in msgs.values())
    sub_msgs = sum(_total(u) for u, sub in msgs.values() if sub)
    peaks = [_total(u) - _num(u.get("output_tokens")) for u, sub in msgs.values() if not sub]
    dur = dur_total
    for did, d in details.items():
        d["tokens"] = sum(_total(u) for u in sub_msgs_by.get(did, {}).values())
    agent_min = sum((sp[1] - sp[0]) / 60 for did, sp in spans.items() if did in details)
    wall_min = dur / 60000 if isinstance(dur, (int, float)) else None
    detail = list(details.values())
    review_agents = sum(1 for d in detail if d["review"])
    for d in detail:
        d.pop("id")
    flow = protocol.analyze(events, carry)
    review_fix_rounds = max(0, (rounds or review_agents) - 1)
    rework = (len(gate_failed) + review_fix_rounds + failed_tests + flow["redispatches"]
              + flow["max_reruns_per_step"])
    clean = review_fix_rounds == 0 and not flow["gate_reruns_after_fail"] and not flow["redispatches"]
    return {
        **flow,
        "main_only_min": max(0.0, wall_min - agent_min) if wall_min is not None else None,
        "rework_actions": rework,
        "first_pass_clean": clean,
        "cost_usd": r.get("total_cost_usd"),
        "wall_min": wall_min,
        "agent_min": agent_min,
        "main_min": max(0.0, wall_min - agent_min) if wall_min is not None else None,
        "cold_starts": subagents,
        "error_kinds": kinds,
        "gate_runs_main": gate_main,
        "gate_runs_sub": gate_sub,
        "cost_main_usd": cost_main,
        "cost_by_role": by_role or None,
        "cost_subagents_usd": cost_sub,
        "cache_hit_rate": cache_hit,
        "output_share": out_share,
        "gate_fail_ratio": len(gate_failed) / len(gate_ids) if gate_ids else None,
        "rereads": rereads,
        "docs_dispatched": docs_dispatched,
        "turns": r.get("num_turns"),
        "is_error": r.get("is_error"),
        "subtype": r.get("subtype"),
        **tokens,
        "tokens_total": sum(tokens.values()),
        "context_peak": max(peaks) if peaks else 0,
        "subagents": subagents,
        "subagent_token_share": sub_msgs / all_msgs if all_msgs else None,
        "tool_errors": tool_errors,
        "skills": sorted(skills),
        "started_at": started,
        "tokens_main": sum(_total(u) for u, sub in msgs.values() if not sub),
        "tokens_subagents": sub_msgs,
        "tool_calls": tool_calls,
        "error_rate": tool_errors / tool_calls if tool_calls else None,
        "test_runs": test_runs,
        "failed_test_runs": failed_tests,
        "review_rounds": rounds or review_agents,
        "subagent_detail": detail,
        "subagent_tokens_median": _median([d["tokens"] for d in detail]),
        "subagent_tool_calls_median": _median([d["tool_calls"] for d in detail]),
        "subagent_errors": sum(d["tool_errors"] for d in detail),
        "assistant_texts": texts,
    }


SUM_KEYS = ("cost_usd", "wall_min", "agent_min", "main_min", "main_only_min", "cold_starts", "gate_runs_main",
            "gate_runs_sub", "cost_main_usd", "cost_subagents_usd", "rereads", "turns", "tokens_total",
            "tokens_main", "tokens_subagents", "tool_calls", "tool_errors", "test_runs", "failed_test_runs",
            "subagents", "subagent_errors", "review_rounds", "main_calls", "main_tokens_post_exec",
            "cache_busts", "waves", "rework_actions", "max_reruns_per_step", "gate_reruns_after_fail",
            "redispatches", "main_edits", "main_reads_before_surveyor", "worker_only_reads",
            "extra_main_gate_runs", "inline_residency", "main_diff_reads", "main_source_reads",
            "kit_script_reads", "agent_file_edits", "retro_rereads") + tuple(f"{k}" for k in MODEL_KEYS)


def _add(vals):
    vals = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return sum(vals) if vals else None


def summarize_phases(paths):
    """One summary over the sessions of a two-phase run: counts and costs add, the rest is recombined."""
    carry = {}
    parts = [summarize(p, carry) for p in paths]
    if len(parts) == 1:
        return parts[0]
    out = dict(parts[0])
    for k in SUM_KEYS:
        out[k] = _add([p.get(k) for p in parts])
    for k in ("subagent_detail", "assistant_texts", "wave_widths"):
        out[k] = [x for p in parts for x in p.get(k) or []]
    roles = [p["cost_by_role"] for p in parts if p.get("cost_by_role")]
    out["cost_by_role"] = {k: sum(r.get(k, 0.0) for r in roles) for k in {x for q in roles for x in q}} if roles else None
    out["skills"] = sorted({x for p in parts for x in p.get("skills") or []})
    out["error_kinds"] = {k: sum(p["error_kinds"][k] for p in parts) for k in ERROR_KINDS}
    out["agents_by_role"] = {r: sum(p["agents_by_role"][r] for p in parts) for r in protocol.ROLES}
    out["dispatch_map"] = sum(out["agents_by_role"][r] > 0 for r in protocol.REQUIRED_ROLES) / len(protocol.REQUIRED_ROLES)
    out["review_coverage"] = parts[-1].get("review_coverage")
    out["context_peak"] = max(p["context_peak"] for p in parts)
    out["main_cache_write"] = max(p["main_cache_write"] for p in parts)
    out["started_at"] = min((p["started_at"] for p in parts if p["started_at"] is not None), default=None)
    out["is_error"] = parts[-1]["is_error"]
    out["subtype"] = parts[-1]["subtype"]
    out["docs_dispatched"] = any(p["docs_dispatched"] for p in parts)
    out["first_pass_clean"] = all(p["first_pass_clean"] for p in parts)
    out["main_violations"] = _add([p["main_violations"] for p in parts])
    out["chief_violations"] = _add([p.get("chief_violations") for p in parts])
    out["returns_total"] = sum(p.get("returns_total") or 0 for p in parts)
    out["returns_ok"] = sum(p.get("returns_ok") or 0 for p in parts)
    out["return_compliance"] = out["returns_ok"] / out["returns_total"] if out["returns_total"] else None
    out["surveyor_first"] = next((p["surveyor_first"] for p in parts if p.get("surveyor_first") is not None), None)
    out["parallel_factor"] = next((p["parallel_factor"] for p in parts if p["parallel_factor"] is not None), None)
    out["ceremony_ratio"] = next((p["ceremony_ratio"] for p in parts if p["ceremony_ratio"] is not None), None)
    calls, errs = out["tool_calls"], out["tool_errors"]
    out["error_rate"] = errs / calls if calls else None
    weights = [p["tokens_total"] for p in parts]
    for k in ("cache_hit_rate", "output_share", "gate_fail_ratio", "subagent_token_share"):
        pairs = [(p[k], w) for p, w in zip(parts, weights) if p.get(k) is not None]
        out[k] = sum(v * w for v, w in pairs) / sum(w for _, w in pairs) if pairs and sum(w for _, w in pairs) else None
    return out


if __name__ == "__main__":
    print(json.dumps(summarize_phases(sys.argv[1:]), indent=2))

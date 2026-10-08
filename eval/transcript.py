"""Summarize a `claude -p --output-format stream-json --verbose` transcript (E1 to E7 inputs, R1, R4)."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

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


def summarize(path):
    msgs = {}  # assistant message id -> (usage, is_subagent); one id spans several events
    tool_errors, subagents, skills, started, result = 0, 0, set(), None, None
    tool_calls, test_ids, test_runs, failed_tests, rounds = 0, set(), 0, 0, 0
    details, awaiting_ts = {}, []  # Agent tool_use id -> detail
    sub_msgs_by = {}  # parent id -> {message id: usage}
    spans = {}  # parent id -> [first, last] event time
    kinds, gate_main, gate_sub = dict.fromkeys(ERROR_KINDS, 0), 0, 0
    texts = []  # main-thread assistant text blocks with their event time
    for n, e in enumerate(_events(path)):
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
        elif kind == "assistant":
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            mid = msg.get("id") or f"anon-{n}"
            msgs[mid] = (usage, parent is not None)
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
                if "gate.py" in json.dumps(inp):
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
    all_msgs = sum(_total(u) for u, _ in msgs.values())
    sub_msgs = sum(_total(u) for u, sub in msgs.values() if sub)
    peaks = [_total(u) - _num(u.get("output_tokens")) for u, sub in msgs.values() if not sub]
    dur = r.get("duration_ms")
    for did, d in details.items():
        d["tokens"] = sum(_total(u) for u in sub_msgs_by.get(did, {}).values())
    agent_min = sum((sp[1] - sp[0]) / 60 for did, sp in spans.items() if did in details)
    wall_min = dur / 60000 if isinstance(dur, (int, float)) else None
    detail = list(details.values())
    review_agents = sum(1 for d in detail if d["review"])
    for d in detail:
        d.pop("id")
    return {
        "cost_usd": r.get("total_cost_usd"),
        "wall_min": wall_min,
        "agent_min": agent_min,
        "main_min": max(0.0, wall_min - agent_min) if wall_min is not None else None,
        "cold_starts": subagents,
        "error_kinds": kinds,
        "gate_runs_main": gate_main,
        "gate_runs_sub": gate_sub,
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


if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1]), indent=2))

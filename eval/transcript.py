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


def summarize(path):
    msgs = {}  # assistant message id -> (usage, is_subagent); one id spans several events
    tool_errors, subagents, skills, started, result = 0, 0, set(), None, None
    for n, e in enumerate(_events(path)):
        kind = e.get("type")
        if started is None and e.get("timestamp"):
            started = _epoch(e["timestamp"])
        if kind == "result":
            result = e
        elif kind == "assistant":
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            msgs[msg.get("id") or f"anon-{n}"] = (usage, e.get("parent_tool_use_id") is not None)
            for b in _blocks(e):
                if b.get("type") != "tool_use":
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                if b.get("name") in SPAWN_TOOLS:
                    subagents += 1
                if b.get("name") == "Skill":
                    name = inp.get("skill") or inp.get("name")
                    if name:
                        skills.add(str(name).lstrip("/"))
        elif kind == "user":
            for b in _blocks(e):
                if b.get("type") == "tool_result" and b.get("is_error") is True:
                    tool_errors += 1
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
    return {
        "cost_usd": r.get("total_cost_usd"),
        "wall_min": dur / 60000 if isinstance(dur, (int, float)) else None,
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
    }


if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1]), indent=2))

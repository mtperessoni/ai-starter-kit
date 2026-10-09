"""Interview metrics of one session (I8 of plan-interview-one-pass): how often the chief stopped for the user, what it
asked, what it reversed, what the agents cost against the context budgets. Offline, stdlib only, transcript events only.
Definitions and targets are in eval/METRICS.md "Interview fields"."""
import json
import re
from datetime import datetime

import protocol

FIELDS = ("user_touchpoints", "repeated_topics", "post_prd_reversals", "sheet_decisions", "docs_gate_reruns",
          "heredoc_commands", "stuck_minutes", "orphans_at_wave_end", "questions_after_plan", "agents_over_150k",
          "interview_to_code_tokens", "budget_violations", "budget_violation_count")
SUM_FIELDS = ("user_touchpoints", "repeated_topics", "docs_gate_reruns", "heredoc_commands", "stuck_minutes",
              "questions_after_plan")
BUDGETS = {"surveyor": 60000, "docs": 80000}
HARD_CAP = 150000
OVERLAP = 0.6
MIN_WORDS = 4

GIT_COMMIT = re.compile(r"\bgit\b[^\n;&|]*\bcommit\b")
DOCS_COMMIT = re.compile(r"\bdocs(?:\([\w./-]+\))?!?:")
HEREDOC = re.compile(r"<<-?\s*['\"]?\w+|\bcat\s*>|\bpython3?(?:\.exe)?\s+-(?:\s|$)")
RULE_ID = re.compile(r"\b[A-Z]{2,}-\d+\b")
SENTENCE = re.compile(r"[^.?!\n]*\?")
WORD = re.compile(r"[a-z0-9]+")
DECISION = re.compile(r"^\*\*(\d+)\.\s", re.M)
REAPED = re.compile(r"reaped:\s*(\d+)")
LEFT = re.compile(r"left:\s*(\d+)")
STOP = frozenset("which should would could that this with have does what when will your their there about "
                 "from into than then them they been being were also only just each other".split())
NOT_PRD_EDIT = ("CHANGELOG.md", "INDEX.md", "README.md")


def _blocks(e):
    msg = e.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _epoch(e):
    ts = e.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _result_text(b):
    c = b.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(str(x.get("text", "")) for x in c if isinstance(x, dict))
    return ""


def _words(q):
    return {w for w in WORD.findall(q.lower()) if len(w) > 3 and w not in STOP}


def sheet_decisions(text):
    """Decision items of a sheet: the `**N. title**` lines, each number once."""
    return len(set(DECISION.findall(text or "")))


def _questions_of(name, inp, parent, text_block):
    out = []
    if name == "AskUserQuestion" and parent is None:
        qs = inp.get("questions")
        items = [q.get("question") for q in qs if isinstance(q, dict)] if isinstance(qs, list) else []
        items = [q for q in items if isinstance(q, str)] or ([inp["question"]] if isinstance(inp.get("question"), str) else [])
        out = items or [""]
    elif text_block is not None and parent is None:
        out = [s.strip() for s in SENTENCE.findall(text_block) if len(s.split()) >= MIN_WORDS]
    return out


def repeated(questions):
    """Questions whose significant words mostly appear in an earlier question."""
    seen, n = [], 0
    for q in questions:
        w = _words(q)
        if len(w) >= 3 and any(len(w & s) / min(len(w), len(s)) >= OVERLAP for s in seen if s):
            n += 1
        seen.append(w)
    return n


def analyze(events, sheet_text=None, telemetry=None):
    touch_open, touchpoints = True, 0
    prd_commit, reversals = False, 0
    questions, q_after, executor_seen = [], 0, False
    failed, reruns, gate_ids, heredocs = set(), 0, {}, 0
    reap_ids, reaped, left, reap_seen = set(), 0, 0, False
    agents, tool_start = {}, {}
    sheet = sheet_text
    for e in events:
        kind, parent, ts = e.get("type"), e.get("parent_tool_use_id"), _epoch(e)
        if parent is not None and ts is not None and parent in agents:
            a = agents[parent]
            a["t0"], a["t1"] = min(a["t0"], ts), max(a["t1"], ts)
        if kind == "result" and parent is None:
            touchpoints += touch_open
        elif kind == "assistant":
            for b in _blocks(e):
                if b.get("type") == "text":
                    for q in _questions_of("", {}, parent, str(b.get("text", ""))):
                        questions.append(q)
                        q_after += executor_seen
                    continue
                if b.get("type") != "tool_use":
                    continue
                name, inp, tid = b.get("name"), b.get("input") if isinstance(b.get("input"), dict) else {}, b.get("id")
                if parent in agents and ts is not None:
                    tool_start[tid] = (parent, ts)
                if name in ("Agent", "Task"):
                    if protocol.role_of(inp) == "executor":
                        executor_seen = True
                    agents[tid] = {"t0": ts if ts is not None else float("inf"), "t1": ts if ts is not None else 0.0,
                                   "tool": 0.0}
                    continue
                qs = _questions_of(name, inp, parent, None)
                if qs:
                    touchpoints += touch_open
                    questions.extend(qs)
                    q_after += executor_seen * len(qs)
                path = str(inp.get("file_path", "")).replace("\\", "/")
                if name in ("Write", "Edit") and path.endswith("/sheet.md") and isinstance(inp.get("content"), str):
                    sheet = inp["content"]
                if name == "Edit" and prd_commit and "/docs/prd/" in "/" + path.lstrip("/") \
                        and not path.endswith(NOT_PRD_EDIT) and RULE_ID.search(str(inp.get("old_string", ""))) \
                        and inp.get("old_string") != inp.get("new_string"):
                    reversals += 1
                if name != "Bash":
                    continue
                cmd = str(inp.get("command", ""))
                heredocs += bool(HEREDOC.search(cmd))
                if GIT_COMMIT.search(cmd):
                    docs = bool(DOCS_COMMIT.search(cmd))
                    prd_commit = prd_commit or (docs and "prd" in cmd.lower())
                    touch_open = touch_open and docs
                if "gate.py" in cmd and not executor_seen:
                    norm = " ".join(cmd.split())
                    reruns += norm in failed
                    gate_ids[tid] = norm
                if "reap" in cmd and ("gates.sh" in cmd or "reap.py" in cmd):
                    reap_ids.add(tid)
                    reap_seen = True
        elif kind == "user":
            for b in _blocks(e):
                if b.get("type") != "tool_result":
                    continue
                tid, text = b.get("tool_use_id"), _result_text(b)
                if tid in gate_ids and (b.get("is_error") is True or "ERROR " in text):
                    failed.add(gate_ids[tid])
                if tid in reap_ids:
                    reaped += sum(int(x) for x in REAPED.findall(text))
                    left += sum(int(x) for x in LEFT.findall(text))
                if tid in tool_start and ts is not None:
                    owner, t0 = tool_start[tid]
                    agents[owner]["tool"] += max(0.0, ts - t0)
                    agents[owner]["t1"] = max(agents[owner]["t1"], ts)
                if tid in agents and ts is not None:
                    agents[tid]["t1"] = max(agents[tid]["t1"], ts)
    stuck = sum(max(0.0, (a["t1"] - a["t0"]) - a["tool"]) for a in agents.values() if a["t0"] != float("inf")) / 60
    stuck_agents = {t.get("agent") for t in telemetry or [] if t.get("ev") == "agent_stuck"}
    orphans = reaped + left if reap_seen else (len(stuck_agents) if stuck_agents else None)
    return {"user_touchpoints": touchpoints, "repeated_topics": repeated(questions),
            "post_prd_reversals": reversals if prd_commit else None,
            "sheet_decisions": sheet_decisions(sheet) if sheet else None, "docs_gate_reruns": reruns,
            "heredoc_commands": heredocs, "stuck_minutes": stuck, "orphans_at_wave_end": orphans,
            "questions_after_plan": q_after}


def _role(d):
    return protocol.role_of({"subagent_type": d.get("type"), "description": d.get("description")})


def budget_violations(detail):
    """One line per agent over its context budget: surveyor, docs apply, and the hard cap for everyone."""
    out = []
    for d in detail or []:
        role, tokens, desc = _role(d), d.get("tokens") or 0, str(d.get("description") or "")
        limit = BUDGETS.get(role)
        if role == "docs" and "apply" not in desc.lower():
            limit = None
        for cap in [c for c in (limit, HARD_CAP) if c]:
            if tokens > cap:
                out.append(f"{role} '{desc}' used {tokens} tokens, over {cap}")
    return out


def detail_metrics(detail):
    """Token metrics from the per-agent detail of the transcript summary."""
    detail = detail or []
    by_role = {}
    for d in detail:
        by_role[_role(d)] = by_role.get(_role(d), 0) + (d.get("tokens") or 0)
    code = by_role.get("executor", 0)
    return {"agents_over_150k": sum((d.get("tokens") or 0) > HARD_CAP for d in detail),
            "interview_to_code_tokens": (by_role.get("surveyor", 0) + by_role.get("docs", 0)) / code if code else None,
            "budget_violations": (v := budget_violations(detail)), "budget_violation_count": len(v)}


def merge(parts):
    """Combine the per-session dicts of a two-phase run; the detail metrics are recomputed by the caller."""
    out = {}
    for k in SUM_FIELDS:
        out[k] = sum(p.get(k) or 0 for p in parts)
    for k in ("post_prd_reversals", "orphans_at_wave_end"):
        vals = [p[k] for p in parts if p.get(k) is not None]
        out[k] = sum(vals) if vals else None
    sheets = [p["sheet_decisions"] for p in parts if p.get("sheet_decisions") is not None]
    out["sheet_decisions"] = sheets[0] if sheets else None
    return out


def dumps(m):
    return json.dumps({k: m.get(k) for k in FIELDS})

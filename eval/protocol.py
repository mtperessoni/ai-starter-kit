"""Protocol and flow metrics of one transcript (I-13): dispatch map, main violations, waves, parallelism."""
import json
import re
from datetime import datetime

ROLES = ("surveyor", "docs", "executor", "reviewer", "recheck")
REQUIRED_ROLES = ("surveyor", "docs", "executor", "reviewer")
SPAWN = {"Agent", "Task"}
EDIT = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
READ = {"Read", "Grep", "Glob"}
FALLBACK = (("surveyor", re.compile(r"survey|impact|confront", re.I)),
            ("recheck", re.compile(r"re-?check", re.I)),
            ("reviewer", re.compile(r"review", re.I)),
            ("docs", re.compile(r"writer|planner|docs|promote", re.I)),
            ("executor", re.compile(r"executor|implement|\bT\d{2}\b", re.I)))
TYPE_RE = re.compile(r"prd-flow-(\w+)")
TASK_RE = re.compile(r"\bT\d{2}\b")
GATE_CMD = re.compile(r"gate\.py|gates\.sh")
LINT_CMD = re.compile(r"\blint\b|ruff|flake8|eslint")
SOURCE_RE = re.compile(r"(^|[\\/])(src|docs|tests)[\\/]")
CODE_RE = re.compile(r"(^|[\\/])(src|tests)[\\/]")
DOC_RE = re.compile(r"(^|[\\/])(docs|changes|specs|\.claude)[\\/]|\.md$")
WORKER_ONLY_RE = re.compile(r"reference[\\/]workers[\\/]|\.claude[\\/]agents[\\/]prd-flow-")
STATE_RE = re.compile(r"\.claude[\\/]prd-flow[\\/]state[\\/]|(^|[\\/])changes[\\/]")
ALLOWED_MAIN_GATE = re.compile(r"--rules|--step\s+plan|\bclose\b")
BUST = 30_000


def role_of(inp):
    """Role of a dispatch: `subagent_type` prd-flow-<role>, else the description and prompt keywords."""
    m = TYPE_RE.fullmatch(str(inp.get("subagent_type") or ""))
    if m and m[1] in ROLES:
        return m[1]
    text = f"{inp.get('description', '')} {str(inp.get('prompt', ''))[:300]}"
    return next((role for role, rx in FALLBACK if rx.search(text)), "other")


def _blocks(e):
    msg = e.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _epoch(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def _call_total(usage):
    return sum(_num(usage.get(k)) for k in ("input_tokens", "cache_read_input_tokens",
                                             "cache_creation_input_tokens"))


def _result_len(b):
    c = b.get("content")
    if isinstance(c, str):
        return len(c)
    return sum(len(x.get("text", "")) for x in c if isinstance(x, dict)) if isinstance(c, list) else 0


def _target(inp):
    return str(inp.get("file_path") or inp.get("path") or inp.get("pattern") or "")


def _command_paths(inp):
    cmd = str(inp.get("command", ""))
    return cmd if re.search(r"\b(cat|head|tail|sed|less)\b", cmd) else ""


def analyze(events):
    """Flow metrics from the parsed events of one session."""
    main_calls, order = {}, 0
    roles = dict.fromkeys(ROLES, 0)
    exec_ids, exec_prompts, redispatch = set(), set(), 0
    outstanding, waves, widths = 0, 0, []
    spans, exec_spans = {}, {}
    surveyor_seen = exec_seen = False
    reads_before = edits = worker_reads = 0
    residency_chars, read_ids = 0, {}
    cmd_runs, cmd_failed, gate_ids = {}, set(), {}
    gate_fail_reruns = extra_gate = 0
    main_gate = {}
    doc_calls = code_calls = 0
    post_exec_tokens = 0
    for e in events:
        kind, parent = e.get("type"), e.get("parent_tool_use_id")
        ts = _epoch(e["timestamp"]) if e.get("timestamp") else None
        if ts is not None and parent:
            sp = spans.setdefault(parent, [ts, ts])
            sp[0], sp[1] = min(sp[0], ts), max(sp[1], ts)
        if kind == "assistant":
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            if parent is None:
                mid = msg.get("id") or f"anon-{order}"
                first = mid not in main_calls
                main_calls[mid] = (usage, exec_seen)
                if first and exec_seen:
                    post_exec_tokens += _call_total(usage) + _num(usage.get("output_tokens"))
            order += 1
            for b in _blocks(e):
                if b.get("type") != "tool_use":
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                name, tgt = b.get("name"), _target(inp)
                if name in SPAWN and parent is None:
                    role = role_of(inp)
                    roles[role] = roles.get(role, 0) + 1
                    surveyor_seen = surveyor_seen or role == "surveyor"
                    if role == "executor":
                        exec_seen = True
                        exec_ids.add(b.get("id"))
                        if outstanding == 0:
                            waves += 1
                            widths.append(0)
                        widths[-1] += 1
                        outstanding += 1
                        card = tuple(sorted(set(TASK_RE.findall(str(inp.get("prompt", ""))))))
                        redispatch += bool(card) and card in exec_prompts
                        exec_prompts.add(card)
                    continue
                if name in EDIT | READ and tgt:
                    if DOC_RE.search(tgt) or STATE_RE.search(tgt):
                        doc_calls += 1
                    elif CODE_RE.search(tgt):
                        code_calls += 1
                if parent is not None:
                    continue
                if name in EDIT and SOURCE_RE.search(tgt) and not STATE_RE.search(tgt):
                    edits += 1
                if name in READ | {"Bash"}:
                    probe = tgt if name != "Bash" else _command_paths(inp)
                    if WORKER_ONLY_RE.search(probe):
                        worker_reads += 1
                    elif not surveyor_seen and SOURCE_RE.search(probe) and not STATE_RE.search(probe):
                        reads_before += 1
                        read_ids[b.get("id")] = True
                if name == "Bash":
                    cmd = " ".join(str(inp.get("command", "")).split())
                    if GATE_CMD.search(cmd) or LINT_CMD.search(cmd):
                        cmd_runs[cmd] = cmd_runs.get(cmd, 0) + 1
                        gate_ids[b.get("id")] = cmd
                        if cmd in cmd_failed:
                            gate_fail_reruns += 1
                        if GATE_CMD.search(cmd):
                            if ALLOWED_MAIN_GATE.search(cmd):
                                main_gate[cmd] = main_gate.get(cmd, 0) + 1
                            else:
                                extra_gate += 1
        elif kind == "user":
            for b in _blocks(e):
                if b.get("type") != "tool_result":
                    continue
                tid = b.get("tool_use_id")
                if tid in exec_ids:
                    outstanding = max(0, outstanding - 1)
                    exec_ids.discard(tid)
                    sp = spans.get(tid)
                    if sp:
                        exec_spans[tid] = sp
                if tid in read_ids:
                    residency_chars += _result_len(b)
                if tid in gate_ids and b.get("is_error") is True:
                    cmd_failed.add(gate_ids[tid])
    plain = cmd_runs
    extra = extra_gate + sum(max(0, n - 1) for n in main_gate.values())
    surveyed = roles["surveyor"] > 0
    violations = (edits + reads_before + worker_reads + extra) if (surveyed or roles["executor"]) else None
    writes = [u.get("cache_creation_input_tokens", 0) for u, _ in main_calls.values()]
    busts = sum(1 for w in writes[1:] if _num(w) > BUST)
    first_usage = next(iter(main_calls.values()), ({}, False))[0]
    start, end = (min(s[0] for s in exec_spans.values()), max(s[1] for s in exec_spans.values())) \
        if exec_spans else (None, None)
    exec_wall = end - start if start is not None else 0
    agent_exec = sum(s[1] - s[0] for s in exec_spans.values())
    required = [roles[r] > 0 for r in REQUIRED_ROLES]
    return {
        "agents_by_role": roles,
        "dispatch_map": sum(required) / len(required),
        "main_calls": len(main_calls),
        "main_tokens_post_exec": post_exec_tokens,
        "main_cache_write": max([_num(w) for w in writes[1:]] or [0]),
        "cache_busts": busts,
        "start_context": _call_total(first_usage) if main_calls else None,
        "main_violations": violations,
        "main_edits": edits, "main_reads_before_surveyor": reads_before,
        "worker_only_reads": worker_reads, "extra_main_gate_runs": extra,
        "inline_residency": residency_chars // 4,
        "waves": waves, "wave_widths": widths,
        "parallel_factor": agent_exec / exec_wall if exec_wall > 0 else None,
        "ceremony_ratio": doc_calls / code_calls if code_calls else None,
        "max_reruns_per_step": max([n - 1 for n in plain.values()] or [0]),
        "gate_reruns_after_fail": gate_fail_reruns,
        "redispatches": redispatch,
    }

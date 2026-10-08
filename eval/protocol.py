"""Protocol and flow metrics of one transcript (I-13): dispatch map, main violations, waves, parallelism."""
import json
import re
import shlex
from datetime import datetime

ROLES = ("surveyor", "docs", "executor", "reviewer", "recheck")
REQUIRED_ROLES = ("surveyor", "docs", "executor", "reviewer")
SPAWN = {"Agent", "Task"}
EDIT = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
READ = {"Read", "Grep", "Glob"}
FALLBACK = (("recheck", re.compile(r"re-?check", re.I)),
            ("executor", re.compile(r"^\s*(fix|apply|implement|execute)\b", re.I)),
            ("reviewer", re.compile(r"review", re.I)),
            ("executor", re.compile(r"executor|implement|\bT\d{2}\b", re.I)),
            ("surveyor", re.compile(r"survey|impact|confront", re.I)),
            ("docs", re.compile(r"writer|planner|docs|promote", re.I)))
TYPE_RE = re.compile(r"prd-flow-(\w+)")
TASK_RE = re.compile(r"\bT\d{2}\b")
GATE_CMD = re.compile(r"gate\.py|gates\.sh")
LINT_CMD = re.compile(r"\blint\b|ruff|flake8|eslint")
SOURCE_RE = re.compile(r"(^|[\\/])(src|docs|tests)[\\/]")
CODE_RE = re.compile(r"(^|[\\/])(src|tests)[\\/]")
ROOTED_SOURCE_RE = re.compile(r"^(src|docs|tests)/")
ROOTED_CODE_RE = re.compile(r"^(src|tests)/")
DOC_RE = re.compile(r"(^|[\\/])(docs|changes|specs|\.claude)[\\/]|\.md$")
WORKER_ONLY_RE = re.compile(r"reference[\\/]workers[\\/]|\.claude[\\/]agents[\\/]prd-flow-"
                            r"|(^|[\\/])(impact|classification|agent-plan|prd-writing|trd-planned)\.md$")
CHIEF_FREE = {"AskUserQuestion", "Skill"}
WAVE_LINE_RE = re.compile(r"^WAVE\s+\d+", re.M)
REVIEW_LINE_RE = re.compile(r"^Review:\s*(.+)$", re.M)
STATE_FILE_RE = re.compile(r"(^|[\\/])state\.md$")
STATE_FILE_MENTION_RE = re.compile(r"(^|[\s'\"/\\])state\.md\b")
CLOSE_DISPATCH_RE = re.compile(r"\bclos(?:e|ing)\b", re.I)
REPO_FILE_RE = re.compile(r"(^|[\\/])repo\.md$")
RETURN_FIELDS = ("Status:", "Files:", "Commit:", "Route:", "Next:")
STATE_RE = re.compile(r"\.claude[\\/]prd-flow[\\/]state[\\/]|(^|[\\/])changes[\\/]")
RULES_CMD = re.compile(r"--rules\b")
CLOSE_CMD = re.compile(r"gates?\.(?:sh|py)\s+close\b")
SETUP_CMD = re.compile(r"gates\.sh\s+(?:context|baseline)\b")
STEP_PLAN_CMD = re.compile(r"--step\s+plan\b")
PRE_EXEC_CMD = re.compile(r"gates\.sh\s+(?:related|lint|ratchet|one)\b")
READ_CMDS = {"cat", "head", "tail", "sed", "less"}
RANGE_ARG = re.compile(r"^[\d,$]+[a-z]*$")
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")
BG_RESULT = re.compile(r"\b(async|background)\b", re.I)
BUST = 30_000
INCOMING_RE = re.compile(r"(^|[\/])docs[\/]incoming[\/]")
KIT_SCRIPT_RE = re.compile(r"(^|[\/])scripts[\/][^\/]+\.(py|sh)$|(^|[\/])(gates?|promote)\.(py|sh)$")
AGENT_FILE_RE = re.compile(r"(^|[\/])(deliveries|impact|pack|execution|review|approved-rules)\.md$")
RETRO_RE = re.compile(r"(^|[\/])retro\.md$")
DIFF_CMD = re.compile(r"\bgit\s+(?:diff|show)\b")
STAT_FLAG = re.compile(r"--(?:stat|name-only|name-status|shortstat|numstat)\b")
FIX_RE = re.compile(r"\bfix(?:es|ing)?\b", re.I)
NON_TASK_RE = re.compile(r"\b(?:close|closing|archive|promote|baseline|compare|gate)\b", re.I)


def role_of(inp):
    """Role of a dispatch: `subagent_type` prd-flow-<role>, else the description keywords only."""
    m = TYPE_RE.fullmatch(str(inp.get("subagent_type") or ""))
    if m and m[1] in ROLES:
        return m[1]
    text = str(inp.get("description", ""))
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


def _text_of(b):
    c = b.get("content")
    if isinstance(c, str):
        return c
    return "\n".join(x.get("text", "") for x in c if isinstance(x, dict)) if isinstance(c, list) else ""


def return_complete(text):
    """Whether the text ends with the five return fields of C6-02, in order, after its last Status line."""
    lines = [x.strip() for x in str(text).splitlines() if x.strip()]
    at = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith(RETURN_FIELDS[0])), None)
    if at is None:
        return False
    for field in RETURN_FIELDS[1:]:
        at = next((i for i in range(at + 1, len(lines)) if lines[i].startswith(field)), None)
        if at is None:
            return False
    return True


def chief_violation(name, rel):
    """Whether a chief tool use is outside the C6-07 allowed set: dispatch, AskUserQuestion, state.md, repo.md."""
    if name in SPAWN or name in CHIEF_FREE:
        return False
    if name in {"Read", "Write", "Edit"} and STATE_FILE_RE.search(rel):
        return False
    return not (name == "Read" and REPO_FILE_RE.search(rel))


def plan_reviews(text, plan):
    """Updates `plan` ({waves, per_wave}) from a state.md write that carries the WAVE or Review lines of `## Plan`."""
    waves = len(WAVE_LINE_RE.findall(text))
    if waves:
        plan["waves"] = waves
    m = REVIEW_LINE_RE.search(text)
    if m:
        plan["per_wave"] = "per wave" in m[1].lower()
        plan.setdefault("waves", 1)


def reviews_required(plan):
    """Reviews the plan's Review line asks for, or None when no plan was written."""
    if "per_wave" not in plan:
        return None
    return plan["waves"] if plan["per_wave"] else 1


def _target(inp):
    return str(inp.get("file_path") or inp.get("path") or inp.get("pattern") or "")


def _targets_index(inp, rel):
    """Whether a Grep aims at INDEX.md by its path or by its glob."""
    return any(str(v or "").replace("\\", "/").endswith("INDEX.md") for v in (rel, inp.get("path"), inp.get("glob")))


def _rel(path, cwd):
    """Path relative to the project root with forward slashes; unchanged when it lies outside it."""
    p = path.replace("\\", "/")
    root = (cwd or "").replace("\\", "/").rstrip("/")
    if root and p.lower().startswith(root.lower() + "/"):
        p = p[len(root) + 1:]
    return p[2:] if p.startswith("./") else p


def _is_source(rel, cwd):
    return bool(ROOTED_SOURCE_RE.search(rel) if cwd else SOURCE_RE.search(rel))


def _is_code(rel, cwd):
    return bool(ROOTED_CODE_RE.search(rel) if cwd else CODE_RE.search(rel))


def _command_paths(inp):
    """Path arguments of the whole `cat|head|tail|sed|less` commands inside a shell line."""
    out = []
    for seg in SEGMENT_SPLIT.split(str(inp.get("command", ""))):
        try:
            tokens = shlex.split(seg)
        except ValueError:
            tokens = seg.split()
        if tokens and tokens[0] in READ_CMDS:
            out += [t for t in tokens[1:] if not t.startswith("-") and not RANGE_ARG.match(t)]
    return out


def _span(child, launch, done):
    """[start, end] of an executor: its child events plus the launch and the completion time."""
    points = [t for t in (launch, done, *(child or ())) if t is not None]
    return [min(points), max(points)] if points else [0, 0]


def _union_length(spans):
    """Total length of the union of [start, end] spans: the time at least one executor was running."""
    total, end = 0.0, None
    for a, b in sorted(spans):
        if end is None or a > end:
            total += b - a
            end = b
        elif b > end:
            total += b - end
            end = b
    return total


def _gate_allowed(cmd, st):
    """Whether a main gate run is one the protocol permits; `st` carries the run history."""
    if RULES_CMD.search(cmd):
        ok = cmd not in st["rules_seen"] or cmd in st["last_failed"]
        st["rules_seen"].add(cmd)
        return ok
    if CLOSE_CMD.search(cmd) or SETUP_CMD.search(cmd):
        return True
    if STEP_PLAN_CMD.search(cmd) and st["docs_seen"] and (not st["plan_step_used"] or cmd in st["last_failed"]):
        st["plan_step_used"] = True
        return True
    return PRE_EXEC_CMD.search(cmd) is not None and not st["exec_seen"]


def analyze(events, carry=None):
    """Flow metrics from the parsed events of one session; `carry` holds the seen roles across the phases of a run."""
    carry = carry if carry is not None else {}
    plan = carry.setdefault("plan", {})
    main_calls, order = {}, 0
    roles = dict.fromkeys(ROLES, 0)
    exec_ids, exec_prompts, redispatch = set(), set(), 0
    outstanding, waves, widths, wave_mid = 0, 0, [], None
    spans, exec_spans, launched, bg_ids, exec_start = {}, {}, set(), set(), {}
    surveyor_seen, exec_seen = carry.get("surveyor", False), carry.get("executor", False)
    gate_state = {"rules_seen": set(), "last_failed": set(), "plan_step_used": False,
                  "docs_seen": carry.get("docs", False), "exec_seen": exec_seen}
    index_grep_used = False
    reads_before = edits = worker_reads = 0
    diff_reads = source_reads = kit_reads = agent_edits = retro_reads = 0
    residency_chars, read_ids = 0, {}
    cmd_runs, cmd_failed, gate_ids = {}, set(), {}
    gate_fail_reruns = extra = 0
    doc_calls = code_calls = 0
    post_exec_tokens = 0
    cwd = None
    closed = carry.get("closed", False)
    chief_bad, first_role, spawn_ids, returns = 0, carry.get("first_role"), set(), {}

    def finish(tid, when):
        nonlocal outstanding
        outstanding = max(0, outstanding - 1)
        exec_ids.discard(tid)
        exec_spans[tid] = _span(spans.get(tid), exec_start.get(tid), when)

    last_child = {}
    for n, e in enumerate(events):
        if e.get("parent_tool_use_id"):
            last_child[e["parent_tool_use_id"]] = n

    for n, e in enumerate(events):
        kind, parent = e.get("type"), e.get("parent_tool_use_id")
        if launched:
            for tid in [t for t in exec_ids if t in launched and (kind == "result" or last_child.get(t, n) < n)]:
                finish(tid, None)
        if cwd is None and isinstance(e.get("cwd"), str):
            cwd = e["cwd"]
        ts = _epoch(e["timestamp"]) if e.get("timestamp") else None
        if ts is not None and parent:
            sp = spans.setdefault(parent, [ts, ts])
            sp[0], sp[1] = min(sp[0], ts), max(sp[1], ts)
        if kind == "assistant":
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            mid = msg.get("id") or f"anon-{order}"
            if parent is None:
                first = mid not in main_calls
                main_calls[mid] = (usage, exec_seen)
                if first and exec_seen:
                    post_exec_tokens += _call_total(usage) + _num(usage.get("output_tokens"))
            order += 1
            for b in _blocks(e):
                if b.get("type") != "tool_use":
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                name = b.get("name")
                tgt = _target(inp)
                rel = _rel(tgt, cwd) if tgt else ""
                if name in EDIT and STATE_FILE_RE.search(rel):
                    plan_reviews(str(inp.get("new_string") or inp.get("content") or ""), plan)
                if name == "Bash" and STATE_FILE_MENTION_RE.search(str(inp.get("command", ""))):
                    plan_reviews(str(inp.get("command", "")).replace("\\n", "\n"), plan)
                if name == "Bash" and CLOSE_CMD.search(str(inp.get("command", ""))):
                    closed = True
                if name in SPAWN and parent is None:
                    role = role_of(inp)
                    first_role = first_role or role
                    spawn_ids.add(b.get("id"))
                    roles[role] = roles.get(role, 0) + 1
                    surveyor_seen = surveyor_seen or role == "surveyor"
                    gate_state["docs_seen"] = gate_state["docs_seen"] or role == "docs"
                    gate_state["exec_seen"] = exec_seen or role == "executor"
                    if inp.get("run_in_background") is True:
                        bg_ids.add(b.get("id"))
                    if role == "executor" and CLOSE_DISPATCH_RE.search(str(inp.get("description", ""))):
                        closed = True
                    if role == "executor":
                        exec_seen = True
                        exec_ids.add(b.get("id"))
                        exec_start[b.get("id")] = ts
                        desc = str(inp.get("description", ""))
                        fix = bool(widths) and FIX_RE.search(desc)
                        non_task = NON_TASK_RE.search(desc) and not TASK_RE.search(desc)
                        if not (fix or non_task):
                            if mid != wave_mid and (outstanding == 0 or not widths):
                                waves += 1
                                widths.append(0)
                            wave_mid = mid
                            widths[-1] += 1
                        outstanding += 1
                        card = tuple(sorted(set(TASK_RE.findall(str(inp.get("prompt", ""))))))
                        redispatch += bool(card) and card in exec_prompts
                        exec_prompts.add(card)
                    continue
                if name in EDIT | READ and rel:
                    if DOC_RE.search(rel) or STATE_RE.search(rel):
                        doc_calls += 1
                    elif _is_code(rel, cwd):
                        code_calls += 1
                if parent is not None:
                    continue
                chief_bad += chief_violation(name, rel)
                if name in EDIT and _is_source(rel, cwd) and not STATE_RE.search(rel):
                    edits += 1
                if name in EDIT and STATE_RE.search(rel) and AGENT_FILE_RE.search(rel):
                    agent_edits += 1
                if name in READ | {"Bash"}:
                    probes = [rel] if name != "Bash" else [_rel(x, cwd) for x in _command_paths(inp)]
                    if name == "Grep" and _targets_index(inp, rel) and not index_grep_used:
                        index_grep_used = True
                    elif any(WORKER_ONLY_RE.search(x) for x in probes):
                        worker_reads += 1
                    elif any(KIT_SCRIPT_RE.search(x) for x in probes):
                        kit_reads += 1
                    elif any(RETRO_RE.search(x) for x in probes):
                        retro_reads += 1
                    elif not surveyor_seen and any(_is_source(x, cwd) and not STATE_RE.search(x)
                                                   and not INCOMING_RE.search(x) for x in probes):
                        reads_before += 1
                        read_ids[b.get("id")] = True
                    elif surveyor_seen and any(_is_code(x, cwd) and not STATE_RE.search(x) for x in probes):
                        source_reads += 1
                if name == "Bash" and surveyor_seen:
                    line = str(inp.get("command", ""))
                    diff_reads += bool(DIFF_CMD.search(line)) and not STAT_FLAG.search(line)
                if name == "Bash":
                    cmd = " ".join(str(inp.get("command", "")).split())
                    if GATE_CMD.search(cmd) or LINT_CMD.search(cmd):
                        cmd_runs[cmd] = cmd_runs.get(cmd, 0) + 1
                        gate_ids[b.get("id")] = cmd
                        if cmd in cmd_failed:
                            gate_fail_reruns += 1
                        if GATE_CMD.search(cmd):
                            extra += not _gate_allowed(cmd, gate_state)
                            gate_state["last_failed"].discard(cmd)
        elif kind == "user":
            results = [b for b in _blocks(e) if b.get("type") == "tool_result"]
            for b in results:
                tid = b.get("tool_use_id")
                if tid in spawn_ids and parent is None:
                    returns[tid] = _text_of(b)
                if tid in exec_ids:
                    text = json.dumps(b.get("content"), default=str)
                    if tid not in launched and (tid in bg_ids or (BG_RESULT.search(text) and len(text) < 600)):
                        launched.add(tid)
                    else:
                        finish(tid, ts)
                if tid in read_ids:
                    residency_chars += _result_len(b)
                if tid in gate_ids:
                    failed = b.get("is_error") is True
                    if failed or "ERROR " in json.dumps(b.get("content"), default=str):
                        gate_state["last_failed"].add(gate_ids[tid])
                    if failed:
                        cmd_failed.add(gate_ids[tid])
            if parent is None and launched:
                dump = json.dumps(e.get("message"), default=str)
                own = {b.get("tool_use_id") for b in results}
                for tid in [t for t in exec_ids if t in launched and t in dump and t not in own]:
                    finish(tid, ts)
    for tid in [t for t in exec_ids if t in launched]:
        exec_spans[tid] = _span(spans.get(tid), exec_start.get(tid), None)
    carry["reviews"] = carry.get("reviews", 0) + roles["reviewer"]
    carry.update(closed=closed, first_role=first_role, surveyor=surveyor_seen, executor=exec_seen, docs=gate_state["docs_seen"])
    violations = (edits + reads_before + worker_reads + extra + diff_reads + source_reads + kit_reads
                  + agent_edits + retro_reads) if (surveyor_seen or exec_seen) else None
    returns_ok = sum(return_complete(t) for t in returns.values())
    writes = [u.get("cache_creation_input_tokens", 0) for u, _ in main_calls.values()]
    busts = sum(1 for w in writes[1:] if _num(w) > BUST)
    first_usage = next(iter(main_calls.values()), ({}, False))[0]
    exec_wall = _union_length(list(exec_spans.values()))
    agent_exec = sum(s[1] - s[0] for s in exec_spans.values())
    required = [roles[r] > 0 for r in REQUIRED_ROLES]
    need = reviews_required(plan)
    return {
        "agents_by_role": roles,
        "review_coverage": min(1.0, carry["reviews"] / need) if need else None,
        "closed": closed,
        "dispatch_map": sum(required) / len(required),
        "main_calls": len(main_calls),
        "main_tokens_post_exec": post_exec_tokens,
        "main_cache_write": max([_num(w) for w in writes[1:]] or [0]),
        "cache_busts": busts,
        "start_context": _call_total(first_usage) if main_calls else None,
        "main_violations": violations,
        "chief_violations": chief_bad if first_role else None,
        "return_compliance": returns_ok / len(returns) if returns else None,
        "returns_total": len(returns), "returns_ok": returns_ok,
        "surveyor_first": first_role == "surveyor" if first_role else None,
        "main_diff_reads": diff_reads, "main_source_reads": source_reads, "kit_script_reads": kit_reads,
        "agent_file_edits": agent_edits, "retro_rereads": retro_reads,
        "main_edits": edits, "main_reads_before_surveyor": reads_before,
        "worker_only_reads": worker_reads, "extra_main_gate_runs": extra,
        "inline_residency": residency_chars // 4,
        "waves": waves, "wave_widths": widths,
        "parallel_factor": agent_exec / exec_wall if exec_wall > 0 else None,
        "ceremony_ratio": doc_calls / code_calls if code_calls else None,
        "max_reruns_per_step": max([n - 1 for n in cmd_runs.values()] or [0]),
        "gate_reruns_after_fail": gate_fail_reruns,
        "redispatches": redispatch,
    }

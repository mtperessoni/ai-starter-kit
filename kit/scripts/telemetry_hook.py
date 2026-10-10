"""Claude Code hook: appends one summarized event line per hook call (RT02 to RT06, RT13).

Never prints, always exits 0, swallows every exception.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

SEP = r"(?:^|[;&|(]|\|\||&&|\n)\s*(?:\w+=\S*\s+)*"
SECRET_KV = re.compile(r"\b(\w*(?:TOKEN|SECRET|PASSWORD|KEY|AUTH)\w*)=(\"[^\"]*\"|'[^']*'|\S*)", re.I)
BEARER = re.compile(r"\bBearer\s+[\w.~+/=-]+", re.I)
PREFIXED = re.compile(r"\b(?:sk-[\w-]+|gh[po]_\w+|AKIA[0-9A-Z]{8,})")
GATE_CLASS = {"related": "test.related", "one": "test.related", "offline": "test.full",
              "integration": "test.full", "full": "test.full", "build": "docker.build", "baseline": "wait.test"}
POLLING = re.compile(r"\b(?:until|while|for)\b[^\n]*\bsleep\s+\d")
EDIT_CMD = re.compile(r"\bsed\s+(?:-\w+\s+)*-i|\bperl\s+(?:-\w+\s+)*-\w*i|\bcat\s*>|\bgit\s+apply\b|\bpatch\s|\bapply_patch\b"
                      r"|\bwrite_text\(|\bopen\([^)]*['\"]w")
CD_TARGET = re.compile(r"(?:\bcd\s+(?:/d\s+)?|\bgit\s+-C\s+)(\"[^\"]+\"|'[^']+'|[^\s;&|]+)")
ABS_PATH = re.compile(r"(?<![\w./:-])(?:[A-Za-z]:[\\/]|/(?=[\w.-]))[^\s'\";&|()<>]+")
MSYS_DRIVE = re.compile(r"^/([A-Za-z])(?:/|$)")
FIELD = {"mode": re.compile(r"\bmode\s*[:=]\s*`?([\w-]+)", re.I),
         "task": re.compile(r"\btask\s*[:=]?\s*`?([A-Za-z]*\d[\w.-]*)", re.I),
         "slug": re.compile(r"\bslug\s*[:=]\s*`?([\w.-]+)", re.I)}
AUTO_BG_MS = 120000
LOOKBACK_BYTES = 262144
RUNNER = re.compile(SEP + r"(?:python\d?\s+-m\s+)?(?:pytest|unittest|jest|vitest|"
                    r"(?:npm|pnpm|yarn)\s+(?:run\s+)?test|go\s+test|cargo\s+test|dotnet\s+test)\b")
TARGET = re.compile(r"(?:\.(?:py|js|ts|tsx|jsx|go|rs|cs)\b|::|\btest_\w+)")
TARGET_ARGS = re.compile(r"\b(?:pytest|jest|vitest|unittest)\b(.*)", re.S)
WRAPPERS = re.compile(r"(^|[;&|(]\s*)(?:(?:env\s+)?(?:\w+=\S*\s+)*(?:rtk\s+(?:proxy\s+)?|timeout\s+\S+\s+|time\s+|nice\s+|nohup\s+|sudo\s+))+")
NOT_IN_HASH = ("description", "timeout", "run_in_background")
LOCK_WAIT_S, LOCK_STALE_S = 5.0, 10.0
STUCK_ALIVE_S, STUCK_IDLE_S, STUCK_SCAN_EVERY_S, STUCK_LOOKBACK = 1800, 600, 60, 1048576
TOOL_EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")


def redact(text):
    text = SECRET_KV.sub(lambda m: m.group(1) + "=***", text)
    return PREFIXED.sub("***", BEARER.sub("Bearer ***", text))


def classify(cmd):
    cmd = WRAPPERS.sub(r"\1", cmd)
    m = re.search(r"scripts/gates\.sh\s+(\w+)", cmd)
    if m:
        cls = GATE_CLASS.get(m.group(1), "shell")
        if cls == "wait.test" and re.search(r"(?:^|\s)--bg\b", cmd):
            cls = "shell"
        return "chain" if cls.startswith("test.") and EDIT_CMD.search(cmd) else cls
    if re.search(r"\btail\s+-\w*f|\bwhile\s+(?:true|:)\b|\bsleep\s+infinity", cmd):
        return "background.unbounded"
    if re.search(SEP + r"docker(?:-compose)?\b", cmd):
        if re.search(r"\bbuild(?:x)?\b", cmd):
            return "docker.build"
        return "docker.run" if re.search(r"\b(?:run|up)\b", cmd) else "docker.other"
    if POLLING.search(cmd):
        return "wait.test"
    if RUNNER.search(cmd):
        if EDIT_CMD.search(cmd):
            return "chain"
        args = TARGET_ARGS.search(cmd)
        return "test.single" if args and TARGET.search(args.group(1)) else "test.full"
    if re.search(SEP + r"(?:pip3?|npm|pnpm|yarn|poetry|uv|cargo|go|apt(?:-get)?|brew)\s+(?:install|add|ci|get|sync)\b", cmd):
        return "install"
    if re.search(SEP + r"git\b", cmd):
        return "git"
    return "shell"


def norm_path(raw, base):
    raw = raw.strip("\"'")
    if os.name == "nt":
        m = MSYS_DRIVE.match(raw)
        if m:
            raw = m.group(1).upper() + ":" + raw[2:]
    raw = os.path.expanduser(raw)
    return os.path.normpath(raw if os.path.isabs(raw) else os.path.join(base, raw))


def tool_targets(p):
    """Directories a tool call works in, in order: the command's cd or -C target, the parent of its file path, then every absolute path
    its Bash command names (Windows drive paths and Git Bash /c/ paths included)."""
    ti = p.get("tool_input")
    if not isinstance(ti, dict):
        return []
    base = p.get("cwd") or os.getcwd()
    raws = []
    if str(p.get("tool_name", "")).lower() == "bash":
        command = str(ti.get("command", ""))
        m = CD_TARGET.search(command)
        if m:
            raws.append(m.group(1))
        raws += [m.group(0) for m in ABS_PATH.finditer(command)]
    else:
        f = ti.get("file_path") or ti.get("path")
        if f:
            raws.append(os.path.dirname(str(f)) or ".")
    return [norm_path(raw, base) for raw in raws if raw]


def kit_root(start):
    here = start
    while True:
        if os.path.isfile(os.path.join(here, "ai-kit.json")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def repo_root(p):
    """The kit root of the call's first target that has one; the session root when none does."""
    for target in tool_targets(p):
        found = kit_root(target)
        if found:
            return found
    return find_root(p.get("cwd"))


def find_back(path, match):
    """Newest event in the tail of the file that satisfies match."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - LOOKBACK_BYTES))
            lines = f.read().splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict) and match(d):
            return d
    return None


def agent_fields(ti):
    prompt = str(ti.get("prompt", ""))
    out = {k: m.group(1) for k, rx in FIELD.items() for m in [rx.search(prompt)] if m}
    if ti.get("model"):
        out["model"] = str(ti["model"])
    out["bg"] = bool(ti.get("run_in_background"))
    return out


def find_root(cwd):
    start = os.path.abspath(cwd or os.getcwd())
    here = start
    while True:
        if os.path.isfile(os.path.join(here, "ai-kit.json")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return start
        here = parent


def branch(runs):
    cache = os.path.join(runs, ".branch")
    try:
        if time.time() - os.path.getmtime(cache) < 60:
            with open(cache, encoding="utf8") as f:
                return f.read().strip()
    except OSError:
        pass
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
                             text=True, timeout=2, cwd=os.path.dirname(os.path.dirname(runs)))
        name = out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        name = ""
    name = name.replace("/", "-")
    if name:
        with open(cache, "w", encoding="utf8") as f:
            f.write(name)
    return name


def context(runs):
    name = os.environ.get("AI_KIT_CONTEXT", "").strip()
    if not name:
        try:
            with open(os.path.join(runs, "current"), encoding="utf8") as f:
                name = f.readline().strip()
        except OSError:
            pass
    return re.sub(r"[^\w.-]", "-", name or branch(runs) or "default") or "default"


def build_event(p, now, path=None):
    ev = p.get("hook_event_name", "")
    e = {"ts": now, "ev": ev, "sid": str(p.get("session_id", ""))[:8],
         "agent": p.get("agent_id") or "main"}
    if p.get("agent_type"):
        e["atype"] = p["agent_type"]
    tool, ti = p.get("tool_name"), p.get("tool_input")
    if tool:
        e["tool"] = tool
        e["tuid"] = p.get("tool_use_id")
        ti = ti if isinstance(ti, dict) else {}
        low = tool.lower()
        if low == "bash":
            raw = str(ti.get("command", ""))
            e["cls"] = classify(raw)
            e["bg"] = bool(ti.get("run_in_background"))
            if ti.get("timeout") is not None:
                e["timeout"] = ti["timeout"]
            elif not e["bg"] and (p.get("duration_ms") or 0) > AUTO_BG_MS:
                e["auto_bg"] = True
        else:
            e["cls"] = "wait.human" if low == "askuserquestion" else low
            raw = str(ti.get("file_path") or ti.get("path") or ti.get("pattern") or ti.get("url")
                      or ti.get("description") or "")
        if tool == "Agent":
            e.update(agent_fields(ti))
        e["cmd"] = redact(raw)[:160]
        same = {k: v for k, v in ti.items() if k not in NOT_IN_HASH}
        e["h"] = hashlib.sha1(json.dumps(same, sort_keys=True).encode()).hexdigest()[:12]
        if low in ("edit", "write", "multiedit") and ti.get("file_path"):
            e["files"] = [ti["file_path"]]
    if "duration_ms" in p:
        e["ms"] = p["duration_ms"]
    if path and ev == "PostToolUse" and str(tool).lower() == "askuserquestion":
        pre = find_back(path, lambda d: d.get("ev") == "PreToolUse" and d.get("tuid") == p.get("tool_use_id"))
        if pre:
            e["wait_ms"] = max(0, int((now - pre["ts"]) * 1000))
    if ev == "PostToolUseFailure":
        e["err"] = True
        e["intr"] = bool(p.get("is_interrupt"))
    resp = p.get("tool_response")
    if resp is not None:
        if isinstance(resp, dict) and ("stdout" in resp or "stderr" in resp):
            size = len(str(resp.get("stdout", ""))) + len(str(resp.get("stderr", "")))
        else:
            size = len(json.dumps(resp))
        e["out_kb"] = round(size / 1024, 1)
        if tool == "Agent" and isinstance(resp, dict):
            e["sub"] = {"tokens": resp.get("totalTokens"), "ms": resp.get("totalDurationMs"),
                        "tools": resp.get("totalToolUseCount"), "status": resp.get("status"),
                        "id": resp.get("agentId")}
    if ev == "SessionStart":
        e["tp"] = p.get("transcript_path")
    if ev == "SubagentStop":
        e["tp"] = p.get("agent_transcript_path")
        start = path and find_back(path, lambda d: d.get("ev") == "SubagentStart" and d.get("agent") == e["agent"])
        if start:
            e["dur_ms"] = max(0, int((now - start["ts"]) * 1000))
        if "background_tasks" in p:
            e["bg"] = len(p.get("background_tasks") or [])
    if p.get("trigger"):
        e["trigger"] = p["trigger"]
    if ev == "PreCompact":
        e["ctx_before"] = p.get("tokens_before") or p.get("context_tokens")
    if ev == "PostCompact":
        e["ctx_after"] = p.get("tokens_after") or p.get("context_tokens")
    if p.get("notification_type"):
        e["ntype"] = p["notification_type"]
        if ev == "Notification" and e["ntype"] in ("permission_prompt", "idle_prompt", "elicitation_dialog"):
            e["cls"] = "wait.human"
    if ev == "Stop":
        e["bg"] = len(p.get("background_tasks") or [])
    ver = p.get("version") or p.get("claude_code_version")
    if ver:
        e["ver"] = ver
    return {k: v for k, v in e.items() if v is not None}


def next_seq(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 8192))
            lines = f.read().splitlines()
        return json.loads(lines[-1])["seq"] + 1
    except Exception:
        return 1


def cap(path, max_mb, now):
    if os.path.getsize(path) <= max_mb * 1024 * 1024:
        return
    with open(path, encoding="utf8") as f:
        lines = f.read().splitlines()
    keep = lines[len(lines) // 2:]
    marker = {"ts": now, "ev": "truncated", "dropped": len(lines) - len(keep)}
    with open(path, "w", encoding="utf8") as f:
        f.write(json.dumps(marker) + "\n" + "\n".join(keep) + "\n")


def scan_stuck(path, now):
    """agent_stuck events for subagents alive past STUCK_ALIVE_S or without a tool event for STUCK_IDLE_S, once per agent and reason."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - STUCK_LOOKBACK))
            lines = f.read().splitlines()
    except OSError:
        return []
    live, reported = {}, set()
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        agent = d.get("agent") if isinstance(d, dict) else None
        if not agent or agent == "main":
            continue
        ev = d.get("ev")
        if ev == "SubagentStart":
            live[agent] = {"start": d["ts"], "last": d["ts"], "atype": d.get("atype"), "sid": d.get("sid")}
        elif ev == "SubagentStop":
            live.pop(agent, None)
        elif ev == "agent_stuck":
            reported.add((agent, d.get("reason")))
        elif ev in TOOL_EVENTS and agent in live:
            live[agent]["last"] = d["ts"]
    out = []
    for agent, a in live.items():
        alive, idle = now - a["start"], now - a["last"]
        for reason, over in (("idle", idle > STUCK_IDLE_S), ("alive", alive > STUCK_ALIVE_S)):
            if over and (agent, reason) not in reported:
                out.append({"ts": now, "ev": "agent_stuck", "sid": a["sid"], "agent": agent, "atype": a["atype"], "reason": reason,
                            "alive_min": round(alive / 60, 1), "idle_min": round(idle / 60, 1)})
    return out


def stuck_events(folder, path, now):
    marker = os.path.join(folder, ".stuck_scan")
    try:
        if now - os.path.getmtime(marker) < STUCK_SCAN_EVERY_S:
            return []
    except OSError:
        pass
    with open(marker, "w", encoding="utf8") as f:
        f.write(str(now))
    return scan_stuck(path, now)


def write_meta(folder, ctx, e):
    path = os.path.join(folder, "meta.json")
    try:
        with open(path, encoding="utf8") as f:
            meta = json.load(f)
    except Exception:
        meta = {}
    meta.setdefault("first_ts", e["ts"])
    meta.update(context=ctx, last_ts=e["ts"])
    sessions = meta.setdefault("sessions", [])
    if e["sid"] and e["sid"] not in sessions:
        sessions.append(e["sid"])
    if e.get("ver"):
        meta["ver"] = e["ver"]
    with open(path, "w", encoding="utf8") as f:
        json.dump(meta, f)


class Lock:
    """Async hooks run in parallel; without it, lines interleave and seq repeats."""

    def __init__(self, path):
        self.path = path
        self.held = False

    def __enter__(self):
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                self.held = True
                return self
            except (FileExistsError, PermissionError):
                # Windows answers PermissionError while another process is deleting the lock.
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_STALE_S:
                        os.remove(self.path)
                        continue
                except OSError:
                    pass
                if time.time() > deadline:
                    return self
                time.sleep(0.005)

    def __exit__(self, *exc):
        if self.held:
            try:
                os.remove(self.path)
            except OSError:
                pass


def main():
    p = json.loads(sys.stdin.read())
    root = repo_root(p)
    runs = os.path.join(root, ".ai-kit", "runs")
    os.makedirs(runs, exist_ok=True)
    ctx = context(runs)
    folder = os.path.join(runs, ctx)
    os.makedirs(folder, exist_ok=True)
    now = time.time()
    path = os.path.join(folder, "events.jsonl")
    e = build_event(p, now, path)
    e["repo"] = root
    max_mb = 5
    try:
        with open(os.path.join(root, "ai-kit.json"), encoding="utf8") as f:
            max_mb = float(json.load(f).get("telemetry", {}).get("max_events_mb", 5))
    except Exception:
        pass
    with Lock(os.path.join(folder, "events.lock")):
        e["seq"] = next_seq(path)
        with open(path, "a", encoding="utf8") as f:
            f.write(json.dumps(e) + "\n")
            for i, extra in enumerate(stuck_events(folder, path, now), 1):
                extra.update(repo=root, seq=e["seq"] + i)
                f.write(json.dumps(extra) + "\n")
        cap(path, max_mb, now)
        if e["ev"] in ("SessionStart", "SessionEnd"):
            write_meta(folder, ctx, e)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        pass
    sys.exit(0)

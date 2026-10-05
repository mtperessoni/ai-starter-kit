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
              "integration": "test.full", "full": "test.full", "build": "docker.build"}
RUNNER = re.compile(SEP + r"(?:python\d?\s+-m\s+)?(?:pytest|unittest|jest|vitest|"
                    r"(?:npm|pnpm|yarn)\s+(?:run\s+)?test|go\s+test|cargo\s+test|dotnet\s+test)\b")
TARGET = re.compile(r"(?:\.(?:py|js|ts|tsx|jsx|go|rs|cs)\b|::|\btest_\w+)")
TARGET_ARGS = re.compile(r"\b(?:pytest|jest|vitest|unittest)\b(.*)", re.S)


def redact(text):
    text = SECRET_KV.sub(lambda m: m.group(1) + "=***", text)
    return PREFIXED.sub("***", BEARER.sub("Bearer ***", text))


def classify(cmd):
    m = re.search(r"scripts/gates\.sh\s+(\w+)", cmd)
    if m:
        return GATE_CLASS.get(m.group(1), "shell")
    if re.search(r"\btail\s+-\w*f|\bwhile\s+(?:true|:)\b|\bsleep\s+infinity", cmd):
        return "background.unbounded"
    if re.search(SEP + r"docker(?:-compose)?\b", cmd):
        if re.search(r"\bbuild(?:x)?\b", cmd):
            return "docker.build"
        return "docker.run" if re.search(r"\b(?:run|up)\b", cmd) else "docker.other"
    if RUNNER.search(cmd):
        args = TARGET_ARGS.search(cmd)
        return "test.single" if args and TARGET.search(args.group(1)) else "test.full"
    if re.search(SEP + r"(?:pip3?|npm|pnpm|yarn|poetry|uv|cargo|go|apt(?:-get)?|brew)\s+(?:install|add|ci|get|sync)\b", cmd):
        return "install"
    if re.search(SEP + r"git\b", cmd):
        return "git"
    return "shell"


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


def build_event(p, now):
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
        else:
            e["cls"] = "wait.human" if low == "askuserquestion" else low
            raw = str(ti.get("file_path") or ti.get("path") or ti.get("pattern") or ti.get("url")
                      or ti.get("description") or "")
        e["cmd"] = redact(raw)[:160]
        e["h"] = hashlib.sha1(json.dumps(ti, sort_keys=True).encode()).hexdigest()[:12]
        if low in ("edit", "write", "multiedit") and ti.get("file_path"):
            e["files"] = [ti["file_path"]]
    if "duration_ms" in p:
        e["ms"] = p["duration_ms"]
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


def main():
    p = json.loads(sys.stdin.read())
    root = find_root(p.get("cwd"))
    runs = os.path.join(root, ".ai-kit", "runs")
    os.makedirs(runs, exist_ok=True)
    ctx = context(runs)
    folder = os.path.join(runs, ctx)
    os.makedirs(folder, exist_ok=True)
    now = time.time()
    e = build_event(p, now)
    path = os.path.join(folder, "events.jsonl")
    e["seq"] = next_seq(path)
    with open(path, "a", encoding="utf8") as f:
        f.write(json.dumps(e) + "\n")
    max_mb = 5
    try:
        with open(os.path.join(root, "ai-kit.json"), encoding="utf8") as f:
            max_mb = float(json.load(f).get("telemetry", {}).get("max_events_mb", 5))
    except Exception:
        pass
    cap(path, max_mb, now)
    if e["ev"] in ("SessionStart", "SessionEnd"):
        write_meta(folder, ctx, e)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        pass
    sys.exit(0)

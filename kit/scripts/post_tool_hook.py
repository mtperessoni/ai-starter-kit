"""PostToolUse and PostToolUseFailure hook: advice the harness adds next to the tool result, never a block.

- Lint after an edit: a detached worker runs ai-kit.json commands.lint_file on the edited code file (only the last edit
  of a burst of post_tool.lint_debounce_s); its findings come back on the next Edit, Write or shell call of the same
  agent, so the edit itself never waits for the linter.
- Failing test streak: consecutive failing test runs per agent; a warning at post_tool.streak_warn, a hand-back at
  post_tool.streak_stop.
- Checkpoint: once per session, when the main thread's context passes post_tool.checkpoint_tokens.
State lives in .ai-kit/runs/_hooks/ (git-ignored). Any error exits 0 silently: the hook must never stop a tool call.
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

DEFAULTS = {"lint_after_edit": True, "lint_timeout_s": 120, "lint_debounce_s": 3, "streak_warn": 3, "streak_stop": 5,
            "checkpoint_tokens": 150000}
EDIT_TOOLS = ("Edit", "Write", "MultiEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
TEST_COMMAND = re.compile(
    r"gates\.sh\s+(one|related|verify|compare|offline|red)\b|\bpytest\b|\bvitest\b|\bjest\b|\bunittest\b"
    r"|\b(npm|yarn|pnpm)\s+(run\s+)?test\b|\bgo\s+test\b|\bcargo\s+test\b"
)
GENERIC_FAILURE = re.compile(r"\b\d+ failed\b|^FAIL\b|^FAILED\b|Tests?:\s+\d+ failed", re.MULTILINE)
TAIL_BYTES = 262144
LINT_LINES = 15


def load_config(root: Path) -> dict | None:
    path = root / "ai-kit.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def matches(relpath: str, patterns: list[str]) -> bool:
    from fnmatch import fnmatchcase
    return any(fnmatchcase(relpath, p) or fnmatchcase("/" + relpath, "*/" + p.removeprefix("**/")) for p in patterns)


def who(payload: dict) -> str:
    return f"{str(payload.get('session_id', ''))[:8]}-{payload.get('agent_id') or 'main'}"


def request_lint(root: Path, cfg: dict, settings: dict, payload: dict) -> None:
    """Starts a detached worker for the edited file; only the last edit of a burst is linted."""
    command = (cfg.get("commands") or {}).get("lint_file") or ""
    if not settings["lint_after_edit"] or "{files}" not in command or command.startswith("<"):
        return
    path = Path(str((payload.get("tool_input") or {}).get("file_path", "")))
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return
    if path.suffix not in cfg.get("code_extensions", []) or matches(rel, cfg.get("generated_patterns", [])):
        return
    key = hashlib.sha1(rel.encode()).hexdigest()[:10]
    req = state_file(root, f"lint-{who(payload)}-{key}.req")
    request_id = str(time.time_ns())
    req.write_text(f"{request_id}\n{rel}", encoding="utf-8")
    flags = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen([sys.executable, __file__, "--lint-worker", str(root), str(req), request_id],  # noqa: S603
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, **flags)


def lint_worker(root: Path, req: Path, request_id: str) -> None:
    settings = {**DEFAULTS, **((load_config(root) or {}).get("post_tool") or {})}
    time.sleep(settings["lint_debounce_s"])
    try:
        current, rel = req.read_text(encoding="utf-8").split("\n", 1)
    except (OSError, ValueError):
        return
    if current != request_id:
        return
    command = (load_config(root) or {}).get("commands", {}).get("lint_file", "")
    source = root / rel
    before = source.stat().st_mtime_ns if source.exists() else 0
    bash = os.environ.get("GATES_BASH") or shutil.which("bash") or "bash"
    try:
        r = subprocess.run([bash, "-c", command.replace("{files}", shlex.quote(rel))], cwd=root, capture_output=True,  # noqa: S603
                           text=True, encoding="utf-8", errors="replace", timeout=settings["lint_timeout_s"])
        result = {"rel": rel, "ok": r.returncode == 0,
                  "lines": [ln[:200] for ln in (r.stdout + r.stderr).splitlines() if ln.strip()][:LINT_LINES]}
    except subprocess.TimeoutExpired:
        result = {"rel": rel, "ok": True, "lines": []}
    fresh = (source.stat().st_mtime_ns if source.exists() else 0) == before
    try:
        if req.read_text(encoding="utf-8").split("\n", 1)[0] == request_id:
            if fresh:
                req.with_suffix(".out").write_text(json.dumps(result), encoding="utf-8")
            req.unlink()
    except OSError:
        return


def lint_findings(root: Path, payload: dict) -> str:
    hooks = root / ".ai-kit" / "runs" / "_hooks"
    if not hooks.is_dir():
        return ""
    out = []
    for f in sorted(hooks.glob(f"lint-{who(payload)}-*.out")):
        try:
            result = json.loads(f.read_text(encoding="utf-8"))
            f.unlink()
        except (OSError, ValueError):
            continue
        if not result.get("ok"):
            out.append(f"Lint of {result['rel']} after your edit found problems; fix them before running tests:\n"
                       + "\n".join(result.get("lines", [])))
    return "\n\n".join(out)


def state_file(root: Path, name: str) -> Path:
    d = root / ".ai-kit" / "runs" / "_hooks"
    d.mkdir(parents=True, exist_ok=True)
    return d / re.sub(r"[^\w.-]", "-", name)


def test_failed(payload: dict, cfg: dict) -> bool:
    if payload.get("hook_event_name") == "PostToolUseFailure":
        return True
    resp = payload.get("tool_response")
    text = f"{resp.get('stdout', '')}\n{resp.get('stderr', '')}" if isinstance(resp, dict) else str(resp or "")
    custom = (cfg.get("tests") or {}).get("failure_regex")
    if custom and re.search(custom, text, re.MULTILINE):
        return True
    return bool(GENERIC_FAILURE.search(text))


def streak_message(root: Path, cfg: dict, settings: dict, payload: dict) -> str:
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if not TEST_COMMAND.search(command):
        return ""
    sid = str(payload.get("session_id", ""))[:8]
    f = state_file(root, f"streak-{sid}-{payload.get('agent_id') or 'main'}")
    count = int(f.read_text(encoding="utf-8") or 0) if f.is_file() else 0
    count = count + 1 if test_failed(payload, cfg) else 0
    f.write_text(str(count), encoding="utf-8")
    if count >= settings["streak_stop"]:
        return (f"{count} test runs in a row failed. Stop editing and hand back now, with the failing test and its error "
                "as a gap; do not try another variation.")
    if count == settings["streak_warn"]:
        return (f"{count} test runs in a row failed. Read the failure itself; if the next run fails the same way, report it "
                "as a gap instead of trying another variation.")
    return ""


def last_context(transcript: str) -> int:
    try:
        with open(transcript, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            fh.seek(max(0, fh.tell() - TAIL_BYTES))
            lines = fh.read().decode("utf-8", errors="ignore").splitlines()
    except OSError:
        return 0
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            usage = (json.loads(line).get("message") or {}).get("usage") or {}
        except ValueError:
            continue
        ctx = sum(usage.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if ctx:
            return ctx
    return 0


def checkpoint_message(root: Path, settings: dict, payload: dict) -> str:
    if payload.get("agent_id") or not payload.get("transcript_path"):
        return ""
    ctx = last_context(payload["transcript_path"])
    budget = settings["checkpoint_tokens"]
    if ctx <= budget:
        return ""
    flag = state_file(root, f"checkpoint-{str(payload.get('session_id', ''))[:8]}")
    if flag.exists():
        return ""
    flag.write_text(str(ctx), encoding="utf-8")
    return (f"Main context is about {ctx // 1000}k tokens, past {budget // 1000}k. Finish the current step, write a short "
            "handoff (done, next, files) and continue in a fresh session.")


def advise(payload: dict) -> str:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    cfg = load_config(root)
    if cfg is None:
        return ""
    settings = {**DEFAULTS, **(cfg.get("post_tool") or {})}
    tool = payload.get("tool_name")
    out = [lint_findings(root, payload)]
    if tool in EDIT_TOOLS and payload.get("hook_event_name") == "PostToolUse":
        request_lint(root, cfg, settings, payload)
    if tool in SHELL_TOOLS:
        out.append(streak_message(root, cfg, settings, payload))
    out.append(checkpoint_message(root, settings, payload))
    return "\n\n".join(m for m in out if m)


def log_error(payload: object) -> None:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or (payload.get("cwd") if isinstance(payload, dict) else None) or ".")
    try:
        with state_file(root, "errors.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {traceback.format_exc(limit=3)}\n")
    except OSError as exc:
        print(f"post_tool_hook: cannot log an error: {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "--lint-worker":
        try:
            lint_worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
        except Exception:  # noqa: BLE001
            log_error({"cwd": sys.argv[2]})
        return 0
    payload: object = {}
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        message = advise(payload) if isinstance(payload, dict) else ""
    except Exception:  # noqa: BLE001
        log_error(payload)
        return 0
    if message:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": payload.get("hook_event_name", "PostToolUse"),
                                                 "additionalContext": message}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Runs a command, streams its output unchanged, returns its exit code and appends one resources line (RT07).

usage: run_probe.py --label <target> [--root <dir>] -- <cmd...>

A probe failure never changes the exit code of the command.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

TAIL_BYTES = 64 * 1024
SAMPLE_SECONDS = 0.2
SECRET_KEY = re.compile(r"(?i)\b([A-Za-z0-9_]*(?:TOKEN|SECRET|PASSWORD|KEY|AUTH)[A-Za-z0-9_]*)=\S+")
SECRET_VALUE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+|\b(?:sk-|ghp_|gho_|AKIA)[A-Za-z0-9_-]*")


def redact(text: str) -> str:
    text = SECRET_KEY.sub(lambda m: f"{m.group(1)}=***", text)
    return SECRET_VALUE.sub("***", text)


def context(root: Path, env: dict | None = None) -> str:
    """RT02: env, .ai-kit/runs/current, git branch with / as -, default."""
    env = os.environ if env is None else env
    if env.get("AI_KIT_CONTEXT", "").strip():
        return env["AI_KIT_CONTEXT"].strip()
    try:
        lines = (root / ".ai-kit" / "runs" / "current").read_text(encoding="utf-8").splitlines()
        if lines and lines[0].strip():
            return lines[0].strip()
    except OSError:
        pass
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
            cwd=root, capture_output=True, text=True, check=False, timeout=5,
        ).stdout.strip()
        if out and out != "HEAD":
            return out.replace("/", "-")
    except (OSError, subprocess.SubprocessError):
        pass
    return "default"


def _counts(text: str) -> dict[str, int]:
    return {word: int(n) for n, word in re.findall(r"(\d+) (failed|passed|skipped|errors?|xfailed|xpassed|total)", text)}


def parse_summary(tail: str) -> tuple[int | None, int | None]:
    """(tests_collected, tests_failed) from the last pytest, unittest, jest or vitest summary in the tail."""
    jest = re.findall(r"^\s*Tests:\s+(.*)$", tail, re.M)
    if jest:
        c = _counts(jest[-1])
        return c.get("total"), c.get("failed", 0)
    ran = re.findall(r"^Ran (\d+) tests? in ", tail, re.M)
    if ran:
        res = re.findall(r"^(?:FAILED|OK)\b(.*)$", tail, re.M)
        failed = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", res[-1])) if res else 0
        return int(ran[-1]), failed
    pytest = re.findall(r"^=*\s*(\d+ (?:failed|passed|skipped|errors?|xfailed|xpassed)[^\n]*?) in [\d.]+s", tail, re.M)
    if pytest:
        c = _counts(pytest[-1])
        failed = c.get("failed", 0) + c.get("error", 0) + c.get("errors", 0)
        collected = sum(v for k, v in c.items() if k != "total")
        return collected, failed
    return None, None


def _win_peak(proc: subprocess.Popen) -> float | None:
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    fn = ctypes.windll.psapi.GetProcessMemoryInfo
    fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    fn.restype = wintypes.BOOL
    handle = wintypes.HANDLE(int(proc._handle))  # type: ignore[attr-defined]  # noqa: SLF001
    return counters.PeakWorkingSetSize / 1048576 if fn(handle, ctypes.byref(counters), counters.cb) else None


def _linux_tree_rss(pid: int) -> float | None:
    children: dict[int, list[int]] = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                stat = (entry / "stat").read_text().rsplit(")", 1)[1].split()
                children.setdefault(int(stat[1]), []).append(int(entry.name))
            except (OSError, IndexError, ValueError):
                continue
    total, stack, seen = 0.0, [pid], set()
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        stack.extend(children.get(p, []))
        try:
            for line in Path(f"/proc/{p}/status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    total += int(line.split()[1]) / 1024
        except (OSError, ValueError):
            continue
    return total


def _sampler(proc: subprocess.Popen):
    """Returns sample() -> MB of the process tree now (or the child's peak on Windows), or None."""
    try:
        import psutil

        top = psutil.Process(proc.pid)

        def sample() -> float | None:
            total = 0.0
            for p in [top, *top.children(recursive=True)]:
                try:
                    total += p.memory_info().rss
                except psutil.Error:
                    continue
            return total / 1048576

        return sample
    except Exception:  # noqa: BLE001
        pass
    if sys.platform.startswith("linux"):
        return lambda: _linux_tree_rss(proc.pid)
    if sys.platform == "win32":
        return lambda: _win_peak(proc)
    return lambda: None


def _pump(src, dst, tail: bytearray, lock: threading.Lock) -> None:
    for chunk in iter(lambda: src.read1(8192), b""):
        try:
            dst.write(chunk)
            dst.flush()
        except (OSError, ValueError):
            pass
        with lock:
            tail += chunk
            if len(tail) > TAIL_BYTES:
                del tail[: len(tail) - TAIL_BYTES]


def _free_gb(root: Path) -> float | None:
    try:
        return round(shutil.disk_usage(root).free / 1e9, 2)
    except OSError:
        return None


def run(label: str, root: Path, cmd: list[str]) -> int:
    started, free_before = time.time(), _free_gb(root)
    # Windows resolves a bare name against System32 first (that is WSL's bash); PATH order is the caller's intent.
    cmd = [shutil.which(cmd[0]) or cmd[0], *cmd[1:]]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
    except OSError as exc:
        print(f"run_probe: cannot start {cmd[0]}: {exc}", file=sys.stderr)
        return 127
    tail, lock, peak = bytearray(), threading.Lock(), None
    threads = [threading.Thread(target=_pump, args=(proc.stdout, sys.stdout.buffer, tail, lock), daemon=True),
               threading.Thread(target=_pump, args=(proc.stderr, sys.stderr.buffer, tail, lock), daemon=True)]
    for t in threads:
        t.start()
    try:
        sample = _sampler(proc)
    except Exception:  # noqa: BLE001
        sample = lambda: None  # noqa: E731

    def take() -> None:
        nonlocal peak
        try:
            mb = sample()
        except Exception:  # noqa: BLE001
            return
        if mb is not None and (peak is None or mb > peak):
            peak = mb

    while proc.poll() is None:
        take()
        time.sleep(SAMPLE_SECONDS)
    take()
    for t in threads:
        t.join(timeout=5)
    code = proc.returncode
    try:
        with lock:
            collected, failed = parse_summary(bytes(tail).decode("utf-8", errors="replace"))
        record = {
            "ts": round(started, 3), "label": label, "cmd": redact(" ".join(cmd))[:160], "exit": code,
            "sec": round(time.time() - started, 2),
            "mem_peak_mb": None if peak is None else round(peak, 1),
            "disk_free_gb_before": free_before, "disk_free_gb_after": _free_gb(root),
            "tests_collected": collected, "tests_failed": failed,
            "agent": os.environ.get("CLAUDE_AGENT_ID") or None,
        }
        folder = root / ".ai-kit" / "runs" / context(root)
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "resources.jsonl").open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:  # noqa: BLE001
        pass
    return code


def main(argv: list[str]) -> int:
    if "--" not in argv:
        print("usage: run_probe.py --label <target> [--root <dir>] -- <cmd...>", file=sys.stderr)
        return 2
    split = argv.index("--")
    parser = argparse.ArgumentParser(prog="run_probe.py")
    parser.add_argument("--label", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv[:split])
    cmd = argv[split + 1 :]
    if not cmd:
        return 2
    return run(args.label, Path(args.root).resolve(), cmd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

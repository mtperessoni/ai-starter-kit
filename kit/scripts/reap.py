#!/usr/bin/env python3
"""Kill the stuck processes of this session, by PID tree, never by image name.

Usage: python scripts/reap.py [--older-than <minutes>] [--dry-run]     (through scripts/gates.sh reap)
A process belongs to this session when it carries this session's shell snapshot id in its command line (Claude Code shell calls source
~/.claude/shell-snapshots/snapshot-*.sh; the id is read from this process's own ancestors) or descends from one that does. It is reaped when
it reads a program from stdin (python -, a heredoc, cat >) or is older than the limit (default 20 minutes). Never reaped: this process and
its ancestors, and any tree rooted at a gates.sh baseline|compare|verify call or scripts/baseline.py.
Prints `reaped: <n>` and `left: 0` or the survivors; exit 1 when a survivor is left.
"""
import json
import os
import re
import subprocess
import sys

DEFAULT_MINUTES = 20.0
SNAPSHOT = re.compile(r"snapshot-[\w.-]*?(?=\.sh\b|[\s'\"]|$)")
PROTECTED = re.compile(r"gates\.sh\s+(?:baseline|compare|verify)\b|scripts[/\\]baseline\.py")
STDIN_WAIT = re.compile(r"(?:^|[\s/\\'\"])(?:python[\d.]*|py|node|perl|ruby)(?:\.exe)?\s+-(?:\s|$)|<<|(?:^|[\s;&|'\"])(?:cat|tee)\s*>")
CIM = ("$ErrorActionPreference='Stop'; $now = Get-Date; "
       "$rows = @(Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{pid=[int]$_.ProcessId; ppid=[int]$_.ParentProcessId; "
       "age=[math]::Round(($now - $_.CreationDate).TotalMinutes, 1); cmd=$_.CommandLine} }); "
       "ConvertTo-Json -InputObject $rows -Compress")


def parse_ps(text):
    rows = []
    for line in text.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 3 or not all(p.isdigit() for p in parts[:3]):
            continue
        rows.append({"pid": int(parts[0]), "ppid": int(parts[1]), "age": int(parts[2]) / 60.0, "cmd": parts[3] if len(parts) > 3 else ""})
    return rows


def parse_cim(text):
    data = json.loads(text)
    data = [data] if isinstance(data, dict) else data
    return [{"pid": int(d["pid"]), "ppid": int(d["ppid"]), "age": float(d["age"] or 0), "cmd": d.get("cmd") or ""} for d in data]


def list_processes():
    if os.name == "nt":
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", CIM], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120, check=False)
        return parse_cim(out.stdout)
    out = subprocess.run(["ps", "-eo", "pid,ppid,etimes,args"], capture_output=True, text=True, errors="replace", timeout=60, check=False)
    return parse_ps(out.stdout)


def descendants(pid, children):
    found, stack = [], [pid]
    while stack:
        for kid in children.get(stack.pop(), []):
            if kid not in found:
                found.append(kid)
                stack.append(kid)
    return found


def kill_tree(pid):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False, timeout=60)
        return
    children = {}
    for p in list_processes():
        children.setdefault(p["ppid"], []).append(p["pid"])
    for target in reversed([pid, *descendants(pid, children)]):
        try:
            os.kill(target, 9)
        except OSError:
            pass


def ancestors(pid, by_pid):
    chain, seen = [], set()
    while pid in by_pid and pid not in seen:
        seen.add(pid)
        chain.append(pid)
        pid = by_pid[pid]["ppid"]
    return chain


def session_id(by_pid, self_pid):
    for pid in ancestors(self_pid, by_pid):
        found = SNAPSHOT.search(by_pid[pid]["cmd"])
        if found:
            return found.group(0)
    return None


def stuck(procs, self_pid, limit):
    """Pids to reap and the roots of their trees, for the session of self_pid."""
    by_pid = {p["pid"]: p for p in procs}
    sid = session_id(by_pid, self_pid)
    if not sid:
        return None, []
    children = {}
    for p in procs:
        children.setdefault(p["ppid"], []).append(p["pid"])
    safe = set(ancestors(self_pid, by_pid))
    for p in procs:
        if PROTECTED.search(p["cmd"]):
            safe.update(ancestors(p["pid"], by_pid))
            safe.update(descendants(p["pid"], children))
    session = set()
    for p in procs:
        if sid in p["cmd"]:
            session.add(p["pid"])
            session.update(descendants(p["pid"], children))
    matched = {pid for pid in session - safe if STDIN_WAIT.search(by_pid[pid]["cmd"]) or by_pid[pid]["age"] >= limit}
    roots = sorted(pid for pid in matched if by_pid[pid]["ppid"] not in matched)
    covered = set()
    for root in roots:
        covered.add(root)
        covered.update(k for k in descendants(root, children) if k not in safe)
    return sid, [(root, sorted(covered & ({root} | set(descendants(root, children))))) for root in roots]


def main(argv, list_processes=list_processes, kill_tree=kill_tree, self_pid=None):
    limit, dry = DEFAULT_MINUTES, "--dry-run" in argv
    if "--older-than" in argv:
        index = argv.index("--older-than")
        try:
            limit = float(argv[index + 1])
        except (IndexError, ValueError):
            print("usage: gates.sh reap [--older-than <minutes>] [--dry-run]", file=sys.stderr)
            return 2
    self_pid = self_pid or os.getpid()
    procs = list_processes()
    sid, trees = stuck(procs, self_pid, limit)
    if sid is None:
        print("reap: no shell snapshot id in the ancestors of this process, nothing is scoped to this session")
        print("reaped: 0")
        print("left: 0")
        return 0
    by_pid = {p["pid"]: p for p in procs}
    targets = [pid for _, members in trees for pid in members]
    if dry:
        for pid in targets:
            print(f"would reap: {pid} {by_pid[pid]['cmd'][:100]}")
        print("reaped: 0")
        return 0
    for root, _ in trees:
        kill_tree(root)
    alive = {p["pid"] for p in list_processes()}
    left = [pid for pid in targets if pid in alive]
    print(f"reaped: {len(targets) - len(left)}")
    if not left:
        print("left: 0")
        return 0
    print(f"left: {len(left)}")
    for pid in left:
        print(f"  {pid} {by_pid[pid]['cmd'][:100]}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

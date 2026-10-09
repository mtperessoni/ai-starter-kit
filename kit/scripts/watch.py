#!/usr/bin/env python3
"""One bounded waiter per wave: the chief starts it in the background and its completion wakes the chief.

Usage: python scripts/watch.py <slug> [--minutes N] [--since <epoch>]     (through scripts/gates.sh watch; N defaults to 30)
Reads the whole run telemetry (.ai-kit/runs/<context>/events.jsonl) and tracks the subagents that started at or after --since (the chief
passes the epoch of the dispatch; default 30 min back) and have no SubagentStop. Prints one line and exits:
  stuck: <agent id> <agent type> idle <n> min     an agent had no tool event for 10 minutes; a silent long command is possible (exit 1)
  deadline: <ids still running>                   N minutes passed (exit 1)
  done: no agent running                          every tracked agent stopped (exit 0)
  unknown: no events file / no SubagentStart seen the events file is missing, or no start was seen within 3 minutes (exit 1)
Scans every 20 s and stops by N minutes: the only sleep loop the kit allows, a script, never model polling.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

SCAN_S = 20
IDLE_S = 600
SINCE_DEFAULT_S = 1800
NO_AGENT_S = 180
DEFAULT_MINUTES = 30.0
TOOL_EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")


def events_path(root, slug):
    runs = Path(root) / ".ai-kit" / "runs"
    name = os.environ.get("AI_KIT_CONTEXT", "").strip()
    if not name:
        try:
            name = (runs / "current").read_text(encoding="utf-8").splitlines()[0].strip()
        except (OSError, IndexError):
            name = ""
    for candidate in (name, slug):
        folder = re.sub(r"[^\w.-]", "-", candidate) if candidate else ""
        if folder and (runs / folder / "events.jsonl").is_file():
            return runs / folder / "events.jsonl"
    return runs / (re.sub(r"[^\w.-]", "-", name or slug) or "default") / "events.jsonl"


def read_rows(path):
    rows = []
    try:
        with open(path, "rb") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        return None
    return rows


def track(rows, since):
    """Agents started at or after `since` and not stopped, with their last tool event; and how many were ever tracked."""
    live, seen = {}, set()
    for row in rows:
        agent, ev, ts = row.get("agent"), row.get("ev"), row.get("ts")
        if not agent or agent == "main" or not isinstance(ts, (int, float)):
            continue
        if ev == "SubagentStart" and ts >= since:
            live[agent] = {"last": ts, "atype": row.get("atype") or "agent"}
            seen.add(agent)
        elif ev == "SubagentStop":
            live.pop(agent, None)
        elif ev in TOOL_EVENTS and agent in live:
            live[agent]["last"] = max(live[agent]["last"], ts)
    return live, seen


def main(argv, root=None, now=time.time, sleep=time.sleep):
    args = list(argv)
    minutes = DEFAULT_MINUTES
    since = None
    if "--minutes" in args:
        index = args.index("--minutes")
        try:
            minutes = float(args[index + 1])
        except (IndexError, ValueError):
            minutes = -1
        del args[index:index + 2]
    if "--since" in args:
        index = args.index("--since")
        try:
            since = float(args[index + 1])
        except (IndexError, ValueError):
            minutes = -1
        del args[index:index + 2]
    if minutes <= 0 or len(args) != 1:
        print("usage: gates.sh watch <slug> [--minutes N] [--since <epoch>]", file=sys.stderr)
        return 2
    root = root or Path(__file__).resolve().parent.parent
    path = events_path(root, args[0])
    launch = now()
    since = launch - SINCE_DEFAULT_S if since is None else since
    while True:
        moment = now()
        rows = read_rows(path)
        if rows is None:
            print("unknown: no events file")
            return 1
        live, seen = track(rows, since)
        if seen and not live:
            print("done: no agent running")
            return 0
        if not seen and moment - launch >= NO_AGENT_S:
            print("unknown: no SubagentStart seen in the events file")
            return 1
        for agent, info in live.items():
            if moment - info["last"] >= IDLE_S:
                print(f"stuck: {agent} {info['atype']} idle {int((moment - info['last']) // 60)} min (a silent long command is possible)")
                return 1
        if moment - launch >= minutes * 60:
            print("deadline: " + " ".join(live) if live else "deadline: none")
            return 1
        sleep(SCAN_S)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

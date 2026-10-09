#!/usr/bin/env python3
"""PreToolUse guard for Bash inside prd-flow subagents.

Blocks commands that destroy sibling work in a shared tree and warns on code
edits made through scripts. Applies only when the hook input names a prd-flow
agent (`agent_type`); the main thread, other agents and unidentified subagents
are never touched. Fails open on any unreadable input or internal error.
"""
import json
import re
import sys

OPT = r"(?:\s+(?:-[Cc]\s+\S+|-c\s+\S+|--\S+))*"
GIT = r"(?:^|[\s;&|(/])git(?:\.exe)?" + OPT + r"\s+"
BLOCKS = [
    (re.compile(GIT + r"stash\b"),
     "git stash hides work from sibling agents in the shared tree. Commit your own paths, or leave the file and report it as a gap."),
    (re.compile(GIT + r"reset\b"),
     "git reset rewrites the shared index or history. Unstage with nothing; stage only your paths with git add <paths>."),
    (re.compile(GIT + r"(?:checkout|switch)\b"),
     "git checkout and git switch change the shared branch or discard paths. Stay on your branch; fix a file by editing it with Edit."),
    (re.compile(GIT + r"restore\b"),
     "git restore discards changes in the shared tree. Revert your own change with Edit."),
    (re.compile(GIT + r"commit\b[^;&|]*--amend\b"),
     "git commit --amend rewrites a commit siblings may build on. Add a new commit instead."),
    (re.compile(r"gates\.sh\s+fix\s*(?:$|[;&|])"),
     "A repo-wide gates.sh fix rewrites files owned by siblings. Run scripts/gates.sh fix <your files>."),
]
WARN_MSG = ("Code edits go through Edit and Write, not sed -i, perl -i, python heredocs or shell redirects. "
            "Scripts may only move code by line range (scripts/move_lines.py). Use Edit or Write for this change.")
SRC = r"\.(?:ts|tsx|js|jsx|mjs|cjs|py|go|rs|java|kt|rb|php|cs|swift|vue|svelte|css|scss|sql)"
WARNS = [
    re.compile(r"(?:^|[\s;&|(])sed\b[^;&|\n]*\s-[A-Za-z]*i"),
    re.compile(r"(?:^|[\s;&|(])perl\b[^;&|\n]*\s-[A-Za-z]*i"),
    re.compile(r"(?:^|[\s;&|(])python[\d.]*\s+-(?:\s|$)"),
    re.compile(r"(?:^|[\s;&|(])python[\d.]*\s+<<"),
    re.compile(r"(?:^|[\s;&|(])(?:cat|tee)\b[^\n]*>>?\s*\S+" + SRC + r"\b[^\n]*<<"),
    re.compile(r"(?:^|[\s;&|(])(?:cat|tee)\b[^\n]*<<[^\n]*>>?\s*\S+" + SRC + r"\b"),
]
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", re.S)
QUOTED = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"")


def heredoc_free(cmd):
    out, pos = [], 0
    for m in HEREDOC.finditer(cmd):
        out.append(cmd[pos:m.start()] + cmd[m.start():cmd.index("\n", m.start())])
        pos = m.end()
    out.append(cmd[pos:])
    return "".join(out)


NESTED = [
    re.compile(r"(?:^|[\s;&|(])(?:ba|z|da|k)?sh\s+(?:-\w+\s+)*-\w*c\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')"),
    re.compile(r"(?:^|[\s;&|(])eval\s+([^\n;&|]+)"),
    re.compile(r"\$\(([^()\n]*)\)"),
    re.compile(r"`([^`\n]*)`"),
]


def nested_payloads(cmd):
    for rx in NESTED:
        for m in rx.finditer(cmd):
            yield m.group(1).strip("\"'")


def blocked_reason(cmd, depth=0):
    text = QUOTED.sub("''", heredoc_free(cmd))
    for rx, why in BLOCKS:
        if rx.search(text):
            return why
    if depth < 3:
        for inner in nested_payloads(heredoc_free(cmd)):
            why = blocked_reason(inner, depth + 1)
            if why:
                return why
    return None


def main():
    try:
        p = json.loads(sys.stdin.read())
        if p.get("tool_name") != "Bash":
            return 0
        cmd = (p.get("tool_input") or {}).get("command") or ""
        if not str(p.get("agent_type") or "").startswith("prd-flow"):
            return 0
        why = blocked_reason(cmd)
        if why:
            sys.stderr.write("Blocked: " + why + "\n")
            return 2
        if any(rx.search(heredoc_free(cmd)) for rx in WARNS):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": WARN_MSG}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)

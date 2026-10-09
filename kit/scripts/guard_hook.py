#!/usr/bin/env python3
"""Blocking PreToolUse guard for Bash and PowerShell, declared in the frontmatter `hooks:` of the prd-flow agents only.

Denies the command shapes that left orphan processes or destroyed sibling work (heredocs, stdin interpreters, shell writes, kills by name,
git commands that rewrite the shared tree). Exit 2 with the reason and the allowed way on stderr blocks the call. Fails open on any
unreadable input or internal error.
"""
import json
import re
import sys

B = r"(?:^|[\s;&|(/\\'\"])"
INTERP = r"(?:python[\d.]*|py|node|perl|ruby|bash|sh)(?:\.exe)?"
GIT = B + r"git(?:\.exe)?(?:\s+(?:-[Cc]\s+\S+|-c\s+\S+|--\S+))*\s+"
WRAPPER = re.compile(B + r"(?:bash|sh|zsh|pwsh|powershell|cmd)(?:\.exe)?\s+(?:-\S+\s+)*(?:-c|-Command|/c)\s", re.I)
CODE_TARGET = re.compile(r"\.(?:py|jsx?|tsx?|mjs|cjs|json|ya?ml|sh|css|scss|html?|md|rst|sql|toml|java|go|rs|rb|php|cs|kt|vue|svelte|cpp|c|h)$", re.I)
REDIRECT = re.compile(r"(?<![-=>\d&<])>>?[ \t]*([^\s;&|)<>]+)")

WRITE_WAY = "Create or change files with Edit and Write (to move code: scripts/gates.sh move <source> <start> <end> <destination>)."
RAW = [
    (re.compile(r"(?:^|[=(|;{,])[ \t]*@['\"][ \t\r]*$|^[ \t]*['\"]@[ \t\r]*$", re.M),
     "A PowerShell here-string breaks on quoting and leaks its delimiters. Write the text to a file with Write, then read the file."),
    (re.compile(r"exec\(\s*(?:sys\.)?stdin\.read"), "A program read from stdin hangs the call. Write the script to a file with Write and run python <file>."),
]
HEREDOC = (re.compile(r"<<<|<<-?[ \t]*(?:''|\"\"|[A-Za-z_\\])"),
           "A heredoc or here-string waits on stdin forever when its delimiter is off, and the process outlives the call. "
           "Put the text in a file with Write, then run the command on that file (a commit message: Write it to a file, then git commit -F <file>).")
RULES = [
    (re.compile(B + INTERP + r"\s+(?:-[A-Za-z]+\s+)*-(?:\s|$)"),
     "An interpreter reading its program from stdin hangs the call. Write the script to a file with Write and run python <file>, or use python -m <module> or python -c."),
    (re.compile(r"\|\s*(?:\S*[/\\])?" + INTERP + r"\s*(?:$|[;&|)])"),
     "Piping into a bare interpreter reads the program from stdin. Write the script to a file with Write and run python <file>, or use python -m <module>."),
    (re.compile(B + r"cat\b[^;&|\n]*?(?<![\d&])>"), "cat with a redirect writes files by shell. " + WRITE_WAY),
    (re.compile(r"(?:^|[|;&(]\s*)tee\b", re.M), "tee writes files by shell. " + WRITE_WAY),
    (re.compile(B + r"(?:Set-Content|Add-Content|Out-File)\b", re.I), "Set-Content, Add-Content and Out-File write files by shell. " + WRITE_WAY),
    (re.compile(B + r"sed\b[^;&|\n]*(?:\s-[A-Za-z]*i|--in-place)"), "sed -i edits files by shell. " + WRITE_WAY),
    (re.compile(B + r"taskkill(?:\.exe)?\b", re.I),
     "taskkill by image name kills every process of that name on the machine, other sessions included. Run scripts/gates.sh reap (it kills by PID tree, only this session's)."),
    (re.compile(r"Stop-Process\b[^;&|\n]*-Name\b|Get-Process\b[^;\n]*Stop-Process", re.I),
     "Stop-Process -Name kills every process of that name on the machine. Run scripts/gates.sh reap (it kills by PID tree, only this session's)."),
    (re.compile(B + r"(?:pkill|killall)\b"),
     "pkill and killall kill by name, other sessions included. Run scripts/gates.sh reap (it kills by PID tree, only this session's)."),
    (re.compile(GIT + r"stash\b"),
     "git stash hides work from sibling agents in the shared tree. Commit only your own paths (git add <paths>, git commit -F <file>), or leave the file and report it as a gap."),
    (re.compile(GIT + r"reset\b"),
     "git reset rewrites the shared index or history. Stage only your paths with git add <paths> and commit with git commit -F <file>."),
    (re.compile(GIT + r"(?:checkout|switch)\b"),
     "git checkout and git switch change the shared branch or discard paths. Stay on your branch; fix a file with Edit and Write, and commit with git commit -F <file>."),
    (re.compile(GIT + r"restore\b"),
     "git restore discards changes in the shared tree. Revert your own change with Edit and Write."),
    (re.compile(GIT + r"commit\b[^;&|]*--amend\b"),
     "git commit --amend rewrites a commit siblings may build on. Add a new commit: Write the message to a file, then git commit -F <file>."),
    (re.compile(GIT + r"commit\b[^;&|\n]*(?:-F\s*-|--file(?:=|\s+)-)(?:\s|$)"),
     "git commit reading its message from stdin hangs the call. Write the message to a file with Write, then git commit -F <file>."),
]
WRAPPED_RULES = range(2, len(RULES))


def strip_quoted(command):
    out, i, n = [], 0, len(command)
    while i < n:
        ch = command[i]
        if ch == "\\" and i + 1 < n:
            out.append(command[i:i + 2])
            i += 2
            continue
        if ch in "'\"":
            j = i + 1
            while j < n and command[j] != ch:
                j += 2 if ch == '"' and command[j] == "\\" else 1
            if j >= n:
                return command
            out.append(ch * 2)
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def redirect_reason(text):
    for target in REDIRECT.findall(text):
        if CODE_TARGET.search(target):
            return "A shell redirect writes a source or doc file. " + WRITE_WAY
    return None


def blocked_reason(command):
    for rx, why in RAW:
        if rx.search(command):
            return why
    text = strip_quoted(command)
    if HEREDOC[0].search(text):
        return HEREDOC[1]
    scans = [(text, range(len(RULES)))]
    if WRAPPER.search(command):
        scans.append((command, WRAPPED_RULES))
    for body, indexes in scans:
        for i in indexes:
            rx, why = RULES[i]
            if rx.search(body):
                return why
        why = redirect_reason(body)
        if why:
            return why
    return None


def main():
    try:
        p = json.loads(sys.stdin.read())
        if p.get("tool_name") not in ("Bash", "PowerShell"):
            return 0
        command = (p.get("tool_input") or {}).get("command") or ""
        why = blocked_reason(str(command))
    except Exception:
        return 0
    if why:
        sys.stderr.write("Blocked: " + why + "\n")
        return 2
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        code = 0
    sys.exit(code)

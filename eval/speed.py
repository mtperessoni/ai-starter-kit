"""Run-speed detectors of one Bash command or tool result (W6.1), used by protocol.analyze."""
import re
import shlex

SEGMENT = re.compile(r"&&|\|\||[;|\n]")
LOOP_SLEEP = re.compile(r"\b(?:until|while|for)\b.*\bsleep\b", re.S)
SEQ_LOOP = re.compile(r"\bfor\b[^;\n]*\bin\b[^;\n]*\bseq\b")
BASELINE_GATE = re.compile(r"gates\.sh\s+baseline\b")
GATE_NARROW = re.compile(r"gates\.sh\s+(?:related|one|lint|ratchet|docs|imports|compare|close|verify)\b")
VERIFY_GATE = re.compile(r"gates\.sh\s+verify\b")
AGENT_GATE = re.compile(r"gates\.sh\s+(?:related|baseline|compare|close|verify|lint|ratchet|docs|imports)\b")
SINGLE_TEST = re.compile(r"\.(?:py|ts|tsx|js|jsx|mjs|go|rs)(?:::\S+)?$")
FULL_RUNNERS = (re.compile(r"\byarn\s+(?:run\s+)?test\b"), re.compile(r"\bnpm\s+(?:run\s+)?test\b"),
                re.compile(r"\bpnpm\s+(?:run\s+)?test\b"), re.compile(r"\bunittest\s+discover\b"),
                re.compile(r"\bgo\s+test\s+\./\.\.\."), re.compile(r"\bcargo\s+test\b"))
PYTEST = re.compile(r"\bpytest\b")
BROAD_DIRS = {"", ".", "./", "tests", "tests/", "test", "test/", "src", "src/"}
CODE_FILE = re.compile(r"\.(?:py|ts|tsx|js|jsx|mjs|go|rs|java|rb|cs|kt|php)\b")
CODE_DIR = re.compile(r"(?:^|[\s'\"=/\\])(?:src|tests)[/\\]")
IN_PLACE = re.compile(r"\bsed\s+(?:-[A-Za-z]+\s+)*-i|\bsed\s+-[A-Za-z]*i|\bperl\s+(?:-[A-Za-z]+\s+)*-[A-Za-z]*i")
PY_RUN = re.compile(r"\bpython3?(?:\.exe)?\s+(?:-\s*<|-\s*$|-c\b|-\s*\n|<<)|\bpython3?(?:\.exe)?\s*<<", re.M)
PY_WRITE = re.compile(r"write_text|write_bytes|\.write\(|open\([^)]*['\"][wax]\+?b?['\"]")
REDIRECT = re.compile(r"(?:>>?|\btee\s+(?:-a\s+)?)\s*['\"]?[^\s'\"|&;<>]+")
GIT_UNSAFE = re.compile(r"\bgit\b(?:\s+-[Cc]\s+\S+)*\s+(?:stash|reset|checkout|switch|restore)\b")
GIT_AMEND = re.compile(r"\bgit\b[^;&|\n]*\bcommit\b[^;&|\n]*--amend\b")
BACKGROUND = re.compile(r"\bnohup\b|(?<![&>])&\s*$|(?<![&>])&\s*(?:\n|;)", re.M)
WAIT = re.compile(r"(?:^|[\s;&])wait\b")
SHELL_ID = re.compile(r"\bID:\s*([\w-]+)|shell[_ ]?id[\"':=\s]+([\w-]+)|task[_ ]?id[\"':=\s]+([\w-]+)", re.I)
CONSUME_TOOLS = {"BashOutput", "TaskOutput", "TaskStop", "KillShell", "KillBash"}
ANSWER = re.compile(r'"[^"]*"\s*=\s*"([^"]*)"')
REJECT = re.compile(r"scenario is wrong|cen[aá]rio est[aá] errado|wrong (?:model|premise|assumption)|premise|"
                    r"not what i|that'?s (?:not right|wrong)|doesn'?t want to proceed|tool use was rejected|"
                    r"user rejected", re.I)


def _segments(cmd):
    return [s for s in SEGMENT.split(cmd) if s.strip()]


def _tokens(seg):
    try:
        return shlex.split(seg)
    except ValueError:
        return seg.split()


def is_full_suite(cmd):
    """Whether a shell line runs `gates.sh baseline|compare` or a whole offline suite (no file or test id narrowing)."""
    if BASELINE_GATE.search(cmd):
        return True
    if GATE_NARROW.search(cmd):
        return False
    if any(rx.search(cmd) for rx in FULL_RUNNERS):
        return True
    for seg in _segments(cmd):
        if not PYTEST.search(seg):
            continue
        args = _tokens(seg)
        args = args[next(i for i, t in enumerate(args) if PYTEST.search(t)) + 1:]
        paths = [a for a in args if not a.startswith("-") and a.strip("'\"")]
        if all(p.strip("'\"") in BROAD_DIRS for p in paths):
            return True
    return False


def is_verify(cmd):
    """A shell line that runs the wave verification `gates.sh verify`."""
    return bool(VERIFY_GATE.search(cmd))


def is_agent_test_run(cmd):
    """A test or gate run other than one named test file: a gates.sh gate, a whole suite, a directory or several files."""
    if AGENT_GATE.search(cmd) or is_full_suite(cmd):
        return True
    for seg in _segments(cmd):
        if not PYTEST.search(seg):
            continue
        args = _tokens(seg)
        args = args[next(i for i, t in enumerate(args) if PYTEST.search(t)) + 1:]
        paths = [a.strip("'\"") for a in args if not a.startswith("-") and a.strip("'\"")]
        if len(paths) != 1 or not SINGLE_TEST.search(paths[0]):
            return True
    return False


def is_poll(cmd):
    """A loop that waits: until, while or for with sleep, or a `for ... in $(seq ...)` loop."""
    return bool(LOOP_SLEEP.search(cmd) or SEQ_LOOP.search(cmd))


def edits_code(cmd):
    """A Bash command that rewrites a source or test file: sed -i, perl -i, a python write, a heredoc or redirect."""
    code = bool(CODE_FILE.search(cmd) or CODE_DIR.search(cmd))
    if not code:
        return False
    if IN_PLACE.search(cmd):
        return True
    if PY_RUN.search(cmd) and PY_WRITE.search(cmd):
        return True
    return any(CODE_FILE.search(m.group(0)) or CODE_DIR.search(" " + m.group(0)) for m in REDIRECT.finditer(cmd))


def is_git_unsafe(cmd):
    return bool(GIT_UNSAFE.search(cmd) or GIT_AMEND.search(cmd))


def detached(cmd):
    """A command that leaves a process running after it returns: nohup or a trailing `&` with no `wait`."""
    return bool(BACKGROUND.search(cmd)) and not WAIT.search(cmd)


def shell_id(text):
    m = SHELL_ID.search(str(text))
    return next((g for g in m.groups() if g), None) if m else None


def consumed_ids(inp):
    """Shell ids a BashOutput, TaskOutput, TaskStop or KillShell call names."""
    return {str(v) for k, v in inp.items() if k in ("bash_id", "shell_id", "task_id", "id") and v}


def rejected(answer_text, is_error):
    """Whether an AskUserQuestion result rejects the premise: a refused tool use or a chosen answer that says so."""
    if is_error and REJECT.search(str(answer_text)):
        return True
    return any(REJECT.search(a) for a in ANSWER.findall(str(answer_text)))

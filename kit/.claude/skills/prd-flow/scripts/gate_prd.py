"""The PRD rows a diff adds or removes."""

from pathlib import Path

from gate_core import ROW, SEPARATOR, cells, git, is_table_line, tokens


def changed_rows(root: Path, base: str, prd_rel: str, pattern: str):
    spec = f":(glob){prd_rel}/{pattern}"
    diff = git(root, "diff", "-U0", base, "--", spec)
    old: dict[str, list[str]] = {}
    new: dict[str, list[str]] = {}
    plain: list[tuple[str, str]] = []
    current = ""
    header_at = -1
    for line in diff.splitlines():
        if line.startswith("+") and SEPARATOR.match(line[1:]) and header_at == len(plain) - 1 >= 0:
            plain.pop()
        header_at = -1
        if line.startswith("+++ "):
            current = line[6:]
            continue
        if line.startswith("---"):
            continue
        m = ROW.match(line[1:]) if line[:1] in "+-" else None
        if m:
            (new if line[0] == "+" else old)[m.group(1)] = cells(m.group(2))
        elif line.startswith("+") and is_table_line(line[1:]) and len(tokens(line)) >= 3:
            plain.append((current, line[1:]))
            header_at = len(plain) - 1
    touched = set(git(root, "diff", "--name-only", base).split())
    touched |= set(git(root, "ls-files", "--others", "--exclude-standard", "docs").split())
    for f in git(root, "ls-files", "--others", "--exclude-standard", "--", spec).split():
        for line in (root / f).read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if m:
                new[m.group(1)] = cells(m.group(2))
    return old, new, touched, plain

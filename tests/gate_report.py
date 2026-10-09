"""Helper for gate tests: the gate prints the errors and a 'warnings: N (see <file>)' line; the warnings are in that file."""

import re

WARNINGS_LINE = re.compile(r"^warnings: (\d+) \(see (\S+)\)$", re.M)


def full(project, result) -> str:
    """stdout of a gate run plus the full report file named on its 'warnings:' line."""
    out = result if isinstance(result, str) else result.stdout
    m = WARNINGS_LINE.search(out)
    path = project.root / m.group(2) if m else None
    return out + "\n" + (path.read_text(encoding="utf-8") if path is not None and path.is_file() else "")

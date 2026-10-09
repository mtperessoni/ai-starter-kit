"""Reserve the next free changes/NNN-<slug> folder, safe against parallel runs.

Usage: python scripts/next_change_number.py <slug>
Prints the created folder. A number is claimed with os.mkdir on changes/.reserve-NNN (it fails when another run holds
it), checked again against the folders of changes/ and changes/archive/, then the real folder is created and the
claim released. A claim left by a crash keeps its number skipped, it is never reused.
"""

import os
import re
import sys
from pathlib import Path

from kit_config import repo_root

NUMBER = re.compile(r"^(?:\.reserve-)?(\d+)(?:-|$)")


def used_numbers(changes: Path) -> set[int]:
    found: set[int] = set()
    for folder in (changes, changes / "archive"):
        if folder.is_dir():
            for entry in folder.iterdir():
                m = NUMBER.match(entry.name)
                if m:
                    found.add(int(m.group(1)))
    return found


def reserve(changes: Path, slug: str) -> Path:
    changes.mkdir(parents=True, exist_ok=True)
    number = max(used_numbers(changes), default=0) + 1
    while True:
        claim = changes / f".reserve-{number:03d}"
        try:
            os.mkdir(claim)
        except FileExistsError:
            number += 1
            continue
        try:
            if any(n == number for n in used_numbers_real(changes)):
                number += 1
                continue
            target = changes / f"{number:03d}-{slug}"
            os.mkdir(target)
            return target
        finally:
            os.rmdir(claim)


def used_numbers_real(changes: Path) -> set[int]:
    found: set[int] = set()
    for folder in (changes, changes / "archive"):
        if folder.is_dir():
            for entry in folder.iterdir():
                m = re.match(r"^(\d+)-", entry.name)
                if m:
                    found.add(int(m.group(1)))
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", argv[0]):
        print("usage: next_change_number.py <slug>   (lowercase letters, digits and dashes)", file=sys.stderr)
        return 2
    root = repo_root()
    target = reserve(root / "changes", argv[0])
    print(target.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

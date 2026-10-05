"""Contract snapshots (rule DS30): each file in ai-kit.json "contracts" must equal what its command prints today.

A snapshot is the one readable copy of the current schema or API contract; agents read it instead of the
migration history. Usage: python scripts/contract_drift.py   (exit 1 on drift or a missing snapshot)
"""

import subprocess
import sys

from kit_config import load, repo_root


def normalized(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def main() -> int:
    root = repo_root()
    contracts = load(root).get("contracts", [])
    if not contracts:
        print("contracts: none configured")
        return 0
    problems = 0
    for contract in contracts:
        path, command = root / contract["file"], contract["command"]
        result = subprocess.run(  # noqa: S602
            command, shell=True, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
        )
        if result.returncode != 0:
            print(f"contracts: {contract['file']}: the command failed ({result.returncode}): {command}")
            problems += 1
        elif not path.exists():
            print(f"contracts: {contract['file']} is missing; write it with: {command}")
            problems += 1
        elif normalized(path.read_text(encoding="utf-8")) != normalized(result.stdout):
            print(f"contracts: {contract['file']} drifted from the code; regenerate it with: {command}")
            problems += 1
    print(f"contracts: {problems} problem(s) in {len(contracts)} snapshot(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

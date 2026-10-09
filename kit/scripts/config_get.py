"""Prints one value of ai-kit.json for gates.sh (no inline interpreter heredocs in the shell script).

Usage: python scripts/config_get.py <section.key> [default]      lists are joined with spaces
       python scripts/config_get.py --has <section.key> <item>   exit 0 when the list holds the item
       python scripts/config_get.py --many <key>...              one run, one `key=value` line per key ("" when unset)
       python scripts/config_get.py --deselect                  the shell-quoted tests.baseline_deselect flags ("" when none)
"""

import sys

from kit_config import load, repo_root


def lookup(config: dict, dotted: str) -> object:
    value: object = config
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def main(argv: list[str]) -> int:
    config = load(repo_root())
    if len(argv) == 3 and argv[0] == "--has":
        listed = lookup(config, argv[1])
        return 0 if isinstance(listed, list) and argv[2] in listed else 1
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--many":
        for key in argv[1:]:
            value = lookup(config, key)
            joined = "" if value is None else " ".join(map(str, value)) if isinstance(value, list) else value
            print(f"{key}={joined}")
        return 0
    if argv == ["--deselect"]:
        from baseline import deselect_args

        print(deselect_args(config.get("tests", {})))
        return 0
    value = lookup(config, argv[0])
    if value is None:
        if len(argv) > 1:
            print(argv[1])
            return 0
        print(f"ai-kit.json has no {argv[0]}", file=sys.stderr)
        return 1
    print(" ".join(map(str, value)) if isinstance(value, list) else value)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

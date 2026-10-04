"""Structure ratchet (docs/code-structure.md AR02, AR03, AR06, AR07): checks what text can see in any stack.

Function and class size, inheritance, closures and import direction belong to the stack's linter.

Usage: python scripts/ratchet.py          check; exit 1 on a violation outside the allowlist
       python scripts/ratchet.py --init   print an allowlist of the current state for ai-kit.json
The allowlist in ai-kit.json only shrinks: an entry that is no longer needed, or that dropped, fails too.
"""

import argparse
import json
import re
import sys
from collections import defaultdict

from kit_config import code_files, is_test, line_count, load, rel, repo_root, stem


def measure(root, cfg) -> dict:
    limits = cfg["limits"]
    id_re = re.compile(cfg["id_pattern"])
    feature_root = root / cfg["feature_root"]
    long_modules, long_tests, banned, no_id = {}, {}, set(), set()
    by_name: dict[str, list[str]] = defaultdict(list)
    for p in code_files(root, cfg):
        r = rel(p, root)
        lines = line_count(p)
        name = stem(p)
        if is_test(r, cfg):
            if lines > limits["test_lines"]:
                long_tests[r] = lines
            continue
        if lines > limits["module_lines"]:
            long_modules[r] = lines
        if name in cfg["banned_names"]:
            banned.add(r)
        if name not in cfg["unique_name_exempt"]:
            by_name[p.name].append(r)
        if feature_root.exists() and p.resolve().is_relative_to(feature_root.resolve()):
            head = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[: limits["id_header_lines"]])
            if lines > 0 and not id_re.search(head) and name not in cfg["unique_name_exempt"]:
                no_id.add(r)
    duplicates = {f"{name}: {', '.join(paths)}" for name, paths in by_name.items() if len(paths) > 1}
    no_map, long_maps = set(), {}
    if feature_root.exists():
        for feature in sorted(d for d in feature_root.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))):
            m = feature / "CLAUDE.md"
            r = rel(feature, root)
            if not m.exists():
                no_map.add(r)
            elif line_count(m) > limits["feature_map_lines"]:
                long_maps[rel(m, root)] = line_count(m)
    return {
        "long_modules": long_modules,
        "long_tests": long_tests,
        "banned_names": banned,
        "duplicate_names": duplicates,
        "no_prd_id": no_id,
        "no_feature_map": no_map,
        "long_feature_maps": long_maps,
    }


def ratchet_counts(what: str, current: dict, allowed: dict) -> list[str]:
    problems = []
    for key, value in sorted(current.items()):
        if key not in allowed:
            problems.append(f"{what}: {key} has {value}, above the limit and not in the allowlist")
        elif value > allowed[key]:
            problems.append(f"{what}: {key} has {value}, above its allowlist entry {allowed[key]}")
    for key, value in sorted(allowed.items()):
        now = current.get(key)
        if now is None:
            problems.append(f"{what}: {key} is gone or within the limit, remove the entry")
        elif now < value:
            problems.append(f"{what}: {key} dropped to {now}, lower the entry from {value}")
    return problems


def ratchet_set(what: str, current: set, allowed: set) -> list[str]:
    problems = [f"{what}: {k} is not in the allowlist" for k in sorted(current - allowed)]
    problems += [f"{what}: {k} is no longer a violation, remove the entry" for k in sorted(allowed - current)]
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="print the allowlist of the current state")
    args = parser.parse_args()
    root = repo_root()
    cfg = load(root)
    current = measure(root, cfg)
    if args.init:
        print(json.dumps({k: (sorted(v) if isinstance(v, set) else v) for k, v in current.items()}, indent=2))
        return 0
    allowed = cfg["allowlist"]
    problems: list[str] = []
    for key, value in current.items():
        if isinstance(value, dict):
            problems += ratchet_counts(key, value, allowed.get(key, {}))
        else:
            problems += ratchet_set(key, value, set(allowed.get(key, [])))
    for line in problems:
        print(line)
    print(f"ratchet: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

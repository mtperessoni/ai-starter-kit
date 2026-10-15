"""Preamble: the fixed context a session or subagent loads before its first action, by part, against a budget.

Parts: the repository's root CLAUDE.md with its @ imports (up to 4 hops), the description of every agent and skill
under .claude/ (the body loads only when used), the user's ~/.claude/CLAUDE.md with its imports, the user's agents and
skills descriptions, and the project's memory index. Sizes are characters; tokens are estimated at 3.5 characters each.
Budgets come from ai-kit.json "preamble" (tokens), else the defaults below. Advisory: exit 0 unless --strict.
Usage: python scripts/preamble.py [--strict]
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_BUDGETS = {
    "repo_instructions": 3500,
    "agent_descriptions": 1500,
    "skill_descriptions": 1500,
    "user_instructions": 2500,
    "user_descriptions": 1500,
    "memory_index": 2000,
}
CHARS_PER_TOKEN = 3.5
MAX_HOPS = 4
IMPORT = re.compile(r"^@(\S+)\s*$", re.MULTILINE)
TOP_KEY = re.compile(r"^[A-Za-z][\w-]*:")


def tokens(chars: int) -> int:
    return round(chars / CHARS_PER_TOKEN)


def project_slug(root: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(root.resolve()))


def memory_index(root: Path, home: Path) -> Path | None:
    projects = home / ".claude" / "projects"
    slug = project_slug(root).lower()
    if projects.is_dir():
        for d in projects.iterdir():
            if d.name.lower() == slug:
                p = d / "memory" / "MEMORY.md"
                return p if p.is_file() else None
    return None


def with_imports(path: Path, home: Path, seen: set, hops: int = 0) -> list[Path]:
    if not path.is_file() or path.resolve() in seen:
        return []
    seen.add(path.resolve())
    found = [path]
    if hops >= MAX_HOPS:
        return found
    for target in IMPORT.findall(path.read_text(encoding="utf-8", errors="ignore")):
        nxt = home / target[2:] if target.startswith("~/") else path.parent / target
        found += with_imports(nxt, home, seen, hops + 1)
    return found


def description(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return ""
    head = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    out, inside = [], False
    for line in head.splitlines():
        if line.startswith("description:"):
            inside = True
            out.append(line[len("description:"):].strip())
        elif inside and TOP_KEY.match(line):
            break
        elif inside:
            out.append(line.strip())
    return " ".join(x for x in out if x)


def descriptions(base: Path) -> tuple[int, list[Path]]:
    files = sorted((base / "agents").glob("*.md")) if (base / "agents").is_dir() else []
    return sum(len(description(p)) for p in files), files


def skill_descriptions(base: Path) -> tuple[int, list[Path]]:
    files = sorted((base / "skills").glob("*/SKILL.md")) if (base / "skills").is_dir() else []
    return sum(len(description(p)) for p in files), files


def chars(paths: list[Path]) -> int:
    return sum(len(p.read_text(encoding="utf-8", errors="ignore")) for p in paths)


def collect(root: Path, home: Path) -> dict:
    repo_files = with_imports(root / "CLAUDE.md", home, set())
    user_files = with_imports(home / ".claude" / "CLAUDE.md", home, set())
    agent_chars, agent_files = descriptions(root / ".claude")
    skill_chars, skill_files = skill_descriptions(root / ".claude")
    ua_chars, ua_files = descriptions(home / ".claude")
    us_chars, us_files = skill_descriptions(home / ".claude")
    mem = memory_index(root, home)
    return {
        "parts": {
            "repo_instructions": chars(repo_files),
            "agent_descriptions": agent_chars,
            "skill_descriptions": skill_chars,
            "user_instructions": chars(user_files),
            "user_descriptions": ua_chars + us_chars,
            "memory_index": chars([mem]) if mem else 0,
        },
        "sources": [str(p) for p in repo_files + agent_files + skill_files + user_files + ua_files + us_files]
        + ([str(mem)] if mem else []),
    }


def measure(root: Path, home: Path) -> dict:
    return collect(root, home)["parts"]


def sources(root: Path, home: Path) -> list[str]:
    return collect(root, home)["sources"]


def warnings(parts: dict, budgets: dict) -> list[str]:
    out = []
    for name, size in parts.items():
        budget = budgets.get(name)
        if budget is not None and tokens(size) > budget:
            out.append(f"preamble: {name} is about {tokens(size)} tokens, over its budget of {budget}")
    return out


def budgets_for(root: Path) -> dict:
    merged = dict(DEFAULT_BUDGETS)
    cfg = root / "ai-kit.json"
    if cfg.is_file():
        merged.update(json.loads(cfg.read_text(encoding="utf-8")).get("preamble", {}))
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--root", default=".")
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    root, home = Path(args.root).resolve(), Path(args.home)
    parts = measure(root, home)
    budgets = budgets_for(root)
    for name, size in parts.items():
        print(f"{name:20} {size:7} chars  ~{tokens(size):5} tokens  budget {budgets.get(name, '-')}")
    print(f"{'total':20} {sum(parts.values()):7} chars  ~{tokens(sum(parts.values())):5} tokens (plus the harness system prompt and tools)")
    warns = warnings(parts, budgets)
    for w in warns:
        print(w)
    return 1 if warns and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())

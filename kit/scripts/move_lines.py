"""Move code by line range, never retyped (rule AR12).

Usage: scripts/gates.sh move <source> <start> <end> <destination> [--at LINE]   (same arguments as this script)
Cuts lines start..end (1-based, inclusive) from source and inserts them into destination before
LINE, or appends them when --at is omitted. Creates destination if it does not exist. The model
decides the map and fixes imports afterwards; this script only moves the bytes.
"""

import argparse
import sys
from pathlib import Path


def read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True) if path.exists() else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--at", type=int, default=None)
    args = parser.parse_args()
    src = read(args.source)
    if not 1 <= args.start <= args.end <= len(src):
        print(f"range {args.start}..{args.end} outside {args.source} ({len(src)} lines)")
        return 2
    block = src[args.start - 1 : args.end]
    if block and not block[-1].endswith("\n"):
        block[-1] += "\n"
    rest = src[: args.start - 1] + src[args.end :]
    dst = rest if args.destination.resolve() == args.source.resolve() else read(args.destination)
    if dst and not dst[-1].endswith("\n"):
        dst[-1] += "\n"
    at = len(dst) if args.at is None else max(0, min(args.at - 1, len(dst)))
    dst = dst[:at] + block + dst[at:]
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    if args.destination.resolve() != args.source.resolve():
        args.source.write_text("".join(rest), encoding="utf-8")
    args.destination.write_text("".join(dst), encoding="utf-8")
    print(f"moved {len(block)} lines: {args.source}:{args.start}-{args.end} -> {args.destination}:{at + 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

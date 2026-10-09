"""Delete Claude Code background task output files that grew without bound.

Task outputs (*.output) live under <temp>/claude/<project slug>/<session>/tasks/. An unbounded one filled the
C: drive once (44 GB). This removes the ones older than 2 days or larger than 200 MB for this repository's
session folders and reports what it removed. Run it by hand, from a hook, or from a scheduler.
A hard cap (default 500 MB) applies to every output under the root, whatever the project: a runaway one is deleted,
or truncated when it is still open and cannot be deleted.
"""

import argparse
import re
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_AGE_DAYS = 2.0
DEFAULT_MAX_MB = 200.0
DEFAULT_HARD_MAX_MB = 500.0


@dataclass(frozen=True)
class Removal:
    path: Path
    size: int
    reason: str
    verb: str = "removed"


def project_slug(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path.resolve()))


def default_slugs(repo: Path) -> list[str]:
    return [project_slug(repo), project_slug(repo.parent)]


def clean(
    root: Path,
    slugs: Sequence[str],
    max_age_days: float,
    max_mb: float,
    now: float | None = None,
    dry_run: bool = False,
    hard_max_mb: float = DEFAULT_HARD_MAX_MB,
) -> tuple[list[Removal], list[str]]:
    moment = time.time() if now is None else now
    removed: list[Removal] = []
    errors: list[str] = []
    done: set[Path] = set()

    def remove(output: Path, size: int, reason: str) -> None:
        verb = "removed"
        try:
            if not dry_run:
                try:
                    output.unlink()
                except OSError:
                    if size <= hard_max_mb * 1024 * 1024:
                        raise
                    output.write_bytes(b"")
                    verb = "truncated"
        except OSError as error:
            errors.append(f"{output}: {error}")
            return
        done.add(output)
        removed.append(Removal(output, size, reason, verb))

    for slug in dict.fromkeys(slugs):
        for output in sorted((root / slug).glob("**/*.output")):
            stat = output.stat()
            reasons = []
            if moment - stat.st_mtime > max_age_days * 86400:
                reasons.append(f"older than {max_age_days:g} days")
            if stat.st_size > max_mb * 1024 * 1024:
                reasons.append(f"larger than {max_mb:g} MB")
            if reasons:
                remove(output, stat.st_size, " and ".join(reasons))
    for output in sorted(root.glob("**/*.output")):
        if output in done:
            continue
        size = output.stat().st_size
        if size > hard_max_mb * 1024 * 1024:
            remove(output, size, f"over the hard cap of {hard_max_mb:g} MB")
    return removed, errors


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(tempfile.gettempdir()) / "claude")
    parser.add_argument("--slug", action="append", help="project folder name under the root (repeatable)")
    parser.add_argument("--max-age-days", type=float, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB)
    parser.add_argument("--hard-max-mb", type=float, default=DEFAULT_HARD_MAX_MB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    slugs = args.slug or default_slugs(Path(__file__).resolve().parents[1])
    removed, errors = clean(args.root, slugs, args.max_age_days, args.max_mb, dry_run=args.dry_run, hard_max_mb=args.hard_max_mb)
    verb = "would remove" if args.dry_run else "removed"
    for item in removed:
        print(f"{verb if args.dry_run else item.verb} {item.path} ({item.size / 1024 / 1024:.1f} MB, {item.reason})")
    print(f"{verb} {len(removed)} files, {sum(i.size for i in removed) / 1024 / 1024:.1f} MB")
    for line in errors:
        print(f"could not remove {line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

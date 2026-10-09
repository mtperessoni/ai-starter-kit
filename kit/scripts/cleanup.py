#!/usr/bin/env python3
"""End-of-run cleanup: nothing of the run outlives it.

Usage: python scripts/cleanup.py [<slug>] [--session-end] [--dry-run]     (through scripts/gates.sh cleanup)
Reaps this session's stuck process trees (reap.py); deletes this project's idle background task outputs (clean_task_outputs.py); deletes
loose files directly in .ai-kit/runs/ (the `current` and `.branch` markers stay); moves state folders untouched for 7 days (not `_*`, not
the given slug) to state/_stale/, deletes _stale/ entries older than 14 days and files of state/_tests and state/_gate older than 3 days.
--session-end does only the first two. Everything except the task outputs stays inside the repository root.
Prints at most 8 lines ending with `left: 0` or the survivors; exit 1 when a survivor is left.
"""
import io
import os
import shutil
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path

import clean_task_outputs
import reap

DAY = 86400.0
STATE_STALE_DAYS = 7
STALE_PURGE_DAYS = 14
CACHE_DAYS = 3
OUTPUT_IDLE_DAYS = 2 / 24
KEEP_MARKERS = ("current", ".branch")
MAX_SURVIVORS = 3
project_slug = clean_task_outputs.project_slug


def inside(root, path):
    try:
        path.resolve().relative_to(root.resolve())
    except (ValueError, OSError):
        return False
    return not path.is_symlink()


def newest(path):
    if path.is_file():
        return path.stat().st_mtime
    times = []
    for base, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
        for name in files:
            try:
                times.append((Path(base) / name).lstat().st_mtime)
            except OSError:
                continue
    return max(times) if times else path.stat().st_mtime


def remove(root, path, dry, errors):
    if not inside(root, path):
        return False
    try:
        if not dry:
            shutil.rmtree(path) if path.is_dir() else path.unlink()
    except OSError as error:
        errors.append(f"{path.name}: {error}")
        return False
    return True


def run_reap(reap_main, dry):
    out = io.StringIO()
    with redirect_stdout(out):
        code = reap_main(["--dry-run"] if dry else [])
    lines = out.getvalue().splitlines()
    reaped = next((ln.split(":", 1)[1].strip() for ln in lines if ln.startswith("reaped:")), "0")
    survivors = [ln.strip() for ln in lines if ln.startswith("  ")] if code else []
    return reaped, survivors


def clean_outputs(root, outputs_root, dry, errors):
    removed, failed = clean_task_outputs.clean(outputs_root, [project_slug(root)], OUTPUT_IDLE_DAYS, clean_task_outputs.DEFAULT_MAX_MB, dry_run=dry, hard_max_mb=None)
    errors.extend(failed)
    return len(removed)


def clean_runs(root, dry, errors):
    runs = root / ".ai-kit" / "runs"
    if not runs.is_dir():
        return 0
    return sum(remove(root, f, dry, errors) for f in sorted(runs.iterdir()) if f.is_file() and f.name not in KEEP_MARKERS)


def clean_state(root, slug, now, dry, errors):
    state = root / ".claude" / "prd-flow" / "state"
    moved = purged = 0
    if not state.is_dir():
        return moved, purged, 0
    stale = state / "_stale"
    for folder in sorted(state.iterdir()):
        if not folder.is_dir() or folder.is_symlink() or folder.name.startswith("_") or folder.name == slug:
            continue
        if now - newest(folder) <= STATE_STALE_DAYS * DAY:
            continue
        if dry:
            moved += 1
            continue
        try:
            stale.mkdir(exist_ok=True)
            if (stale / folder.name).exists():
                shutil.rmtree(stale / folder.name)
            shutil.move(str(folder), str(stale / folder.name))
            moved += 1
        except OSError as error:
            errors.append(f"{folder.name}: {error}")
    if stale.is_dir():
        for entry in sorted(stale.iterdir()):
            if now - newest(entry) > STALE_PURGE_DAYS * DAY and remove(root, entry, dry, errors):
                purged += 1
    caches = 0
    for name in ("_tests", "_gate"):
        folder = state / name
        if not folder.is_dir() or folder.is_symlink():
            continue
        for base, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
            for file in files:
                path = Path(base) / file
                try:
                    old = now - path.lstat().st_mtime > CACHE_DAYS * DAY
                except OSError:
                    continue
                if old and remove(root, path, dry, errors):
                    caches += 1
    return moved, purged, caches


def main(argv, root=None, outputs_root=None, reap_main=reap.main, now=None):
    root = root or Path(__file__).resolve().parent.parent
    outputs_root = outputs_root or Path(tempfile.gettempdir()) / "claude"
    dry, session_end = "--dry-run" in argv, "--session-end" in argv
    slug = next((a for a in argv if not a.startswith("-")), "")
    now = time.time() if now is None else now
    errors = []
    reaped, survivors = run_reap(reap_main, dry)
    outputs = clean_outputs(root, outputs_root, dry, errors)
    verb = "would " if dry else ""
    lines = [f"cleanup{' ' + slug if slug else ''}{' (session end)' if session_end else ''}{' (dry run)' if dry else ''}",
             f"{verb}reaped: {reaped}, task outputs {verb}removed: {outputs}"]
    if not session_end:
        runs = clean_runs(root, dry, errors)
        moved, purged, caches = clean_state(root, slug, now, dry, errors)
        lines.append(f"{verb}removed: {runs} loose run file(s), {caches} cache file(s)")
        lines.append(f"state {verb}moved to _stale: {moved}, purged: {purged}")
    left = survivors + [f"error {e}" for e in errors]
    if not left:
        lines.append("left: 0")
    else:
        lines.append(f"left: {len(left)}")
        lines += [f"  {item[:100]}" for item in left[:MAX_SURVIVORS]]
        if len(left) > MAX_SURVIVORS:
            lines.append(f"  ... {len(left) - MAX_SURVIVORS} more")
    print("\n".join(lines[:8]))
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

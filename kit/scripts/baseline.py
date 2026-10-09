"""Records the baseline failures of the offline suite at a commit, in a throwaway git worktree (TS43).

Usage: python scripts/baseline.py <slug> [--commit REF] [--wait SECONDS]     (through scripts/gates.sh baseline)
A normal foreground command: the chief launches it as a background Bash (run_in_background) and gets a completion event. --bg (detached, no event) is kept for compatibility and not recommended.
The result is cached by commit plus lockfile, test command and deselect list hash under .claude/prd-flow/state/_baseline/, so a second slug at
the same commit costs nothing. A lock file per commit makes a concurrent run wait for the first one. A watchdog kills a run whose log has not grown
for tests.baseline_idle_seconds. Writes .claude/prd-flow/state/<slug>/baseline-failures.txt, baseline.log and baseline.status.
Exit 0 recorded (cached or not), 2 usage or setup problem, 3 the watchdog killed the run (the partial failures are still written, nothing is cached).
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from kit_config import load, repo_root
from new_failures import NO_SUMMARY, failures, has_summary

LOCKFILES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "uv.lock", "poetry.lock", "Pipfile.lock", "requirements.txt",
             "Cargo.lock", "go.sum", "composer.lock", "Gemfile.lock", "gradle.lockfile", "packages.lock.json")
LINKED_DIRS = ("node_modules", ".venv", "venv")
STALE_LOCK_SECONDS = 60
HEARTBEAT_SECONDS = 5
DEFAULT_IDLE_SECONDS = 300
DEFAULT_WAIT_SECONDS = 1800
HUNG = 3
NODE_RUNNER = re.compile(r"\b(vitest|jest|mocha|yarn|npm|pnpm|npx|bun)\b")


class SetupError(Exception):
    pass


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)  # noqa: S603, S607


def cache_key(root: Path, commit: str, command: str, deselect: list[str]) -> str:
    digest = hashlib.sha1(usedforsecurity=False)
    for name in LOCKFILES:
        shown = git(root, "show", f"{commit}:{name}")
        if shown.returncode == 0:
            digest.update(name.encode() + shown.stdout.encode())
    digest.update(command.encode() + "\n".join(deselect).encode())
    return f"{commit[:12]}-{digest.hexdigest()[:12]}"


REPARSE_POINT = 0x400


def is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    if hasattr(os.path, "isjunction"):
        return os.path.isjunction(path)
    if os.name == "nt":
        try:
            return bool(getattr(os.lstat(path), "st_file_attributes", 0) & REPARSE_POINT)
        except OSError:
            return False
    return False


def drop_links(tree: Path) -> None:
    """Remove only the link itself, so deleting a worktree never reaches a real node_modules or .venv behind it."""
    for name in LINKED_DIRS:
        path = tree / name
        if not is_link(path):
            continue
        try:
            if os.name == "nt":
                os.rmdir(path)
            else:
                path.unlink()
        except OSError:
            os.rmdir(path)


def make_link(source: Path, link: Path) -> bool:
    if os.name == "nt":
        made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(source)], capture_output=True, check=False)  # noqa: S603, S607
        return made.returncode == 0
    try:
        os.symlink(source, link, target_is_directory=True)
    except OSError:
        return False
    return True


def lockfiles_match(root: Path, commit: str) -> bool:
    """True when every lockfile of the commit equals the one in the main tree, and no other lockfile exists there."""
    for name in LOCKFILES:
        shown, current = git(root, "show", f"{commit}:{name}"), root / name
        if shown.returncode != 0:
            if current.is_file():
                return False
            continue
        if not current.is_file() or current.read_text(encoding="utf-8", errors="replace") != shown.stdout:
            return False
    return True


def link_dependencies(root: Path, tree: Path, commit: str) -> bool:
    """Link the main tree's installed dependency folders into the worktree when the lockfiles agree: no install per baseline."""
    if not lockfiles_match(root, commit):
        return False
    linked = False
    for name in LINKED_DIRS:
        source = root / name
        if source.is_dir() and not is_link(source) and not (tree / name).exists():
            linked = make_link(source, tree / name) or linked
    return linked


def deselect_args(tests: dict) -> str:
    flag = tests.get("baseline_deselect_flag", "--deselect")
    return "".join(f" {flag} {shlex_quote(item)}" for item in tests.get("baseline_deselect", [])).strip()


def remove_worktree(root: Path, tree: Path) -> None:
    drop_links(tree)
    git(root, "worktree", "remove", "--force", str(tree))
    if tree.exists():
        drop_links(tree)
        shutil.rmtree(tree, ignore_errors=True)
    git(root, "worktree", "prune")


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)  # noqa: S603, S607
    else:
        import signal

        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()
    proc.wait()


def watched(command: str, cwd: Path, env: dict, log: Path, idle: float, beat: Path | None = None) -> tuple[int, bool]:
    """Run a shell command with its output in log; kill it when the log does not grow for idle seconds."""
    bash = os.environ.get("GATES_BASH") or shutil.which("bash") or "bash"
    flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with log.open("wb") as out:
        proc = subprocess.Popen([bash, "-c", command], cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT, **flags)  # noqa: S603
        size, changed, last_beat = -1, time.time(), 0.0
        while proc.poll() is None:
            now = time.time()
            current = log.stat().st_size
            if current != size:
                size, changed = current, now
            if beat is not None and now - last_beat >= HEARTBEAT_SECONDS:
                beat.touch()
                last_beat = now
            if now - changed > idle:
                kill_tree(proc)
                return HUNG, True
            time.sleep(0.25)
        return proc.returncode, False


def acquire(lock: Path, deadline: float, ready: Path) -> bool:
    """True when this process holds the lock; False when another run finished the same result meanwhile."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            lock.write_text(f"{os.getpid()} {int(time.time())}\n", encoding="utf-8")
            return True
        except FileExistsError:
            pass
        if ready.is_file():
            return False
        try:
            if time.time() - lock.stat().st_mtime > STALE_LOCK_SECONDS:
                lock.unlink(missing_ok=True)
                continue
        except OSError:
            continue
        if time.time() > deadline:
            raise TimeoutError(f"baseline lock {lock.name} still held after the wait limit")
        time.sleep(1)


def publish(source: Path, target: Path, status: str) -> int:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / "failures.txt", target / "baseline-failures.txt")
    shutil.copyfile(source / "run.log", target / "baseline.log")
    (target / "baseline.status").write_text(status, encoding="utf-8")
    count = len([line for line in (target / "baseline-failures.txt").read_text(encoding="utf-8").splitlines() if line.strip()])
    print(f"baseline failures: {count} ({status.strip()}, log: {target.as_posix()}/baseline.log)")
    return 0


def fast_flags(tests: dict) -> str:
    """tests.fast_flags (for example "--no-cov -n auto") when the project declares them; never assumed."""
    value = tests.get("fast_flags", "")
    return " ".join(map(str, value)) if isinstance(value, list) else str(value or "")


def run_suite(root: Path, config: dict, commit: str, work: Path) -> tuple[int, bool]:
    commands, tests = config["commands"], config.get("tests", {})
    command = " ".join(filter(None, [str(commands["test"]), str(commands.get("offline_args", "")), fast_flags(tests)]))
    if tests.get("baseline_deselect") and "baseline_deselect_flag" not in tests and NODE_RUNNER.search(command):
        raise SetupError("tests.baseline_deselect is set but tests.baseline_deselect_flag is not: --deselect is pytest only")
    command += " " + deselect_args(tests) if tests.get("baseline_deselect") else ""
    env = {k: v for k, v in os.environ.items() if k not in set(commands.get("offline_unset", []))}
    env[str(commands.get("offline_flag", "OFFLINE_ONLY"))] = "1"
    idle = float(tests.get("baseline_idle_seconds", DEFAULT_IDLE_SECONDS))
    tree = Path(tempfile.mkdtemp(prefix="baseline-"))
    added = git(root, "worktree", "add", "--detach", str(tree), commit)
    if added.returncode != 0:
        shutil.rmtree(tree, ignore_errors=True)
        raise SetupError(f"git worktree add: {added.stderr.strip()}")
    try:
        setup = str(commands.get("setup", ""))
        linked = tests.get("baseline_link_deps", True) and link_dependencies(root, tree, commit)
        if not linked and tests.get("baseline_setup", True) and setup and not setup.startswith("<"):
            code, hung = watched(setup, tree, env, work / "setup.log", max(idle, 600))
            if code != 0:
                raise SetupError(f"setup exit {code}, log {(work / 'setup.log').as_posix()}")
        code, hung = watched(command, tree, env, work / "run.log", idle)
    finally:
        remove_worktree(root, tree)
    return code, hung


def shlex_quote(value: str) -> str:
    return value if re.fullmatch(r"[\w@%+=:,./-]+", value) else "'" + value.replace("'", "'\"'\"'") + "'"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--bg", action="store_true")
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--wait", type=float, default=DEFAULT_WAIT_SECONDS)
    args = parser.parse_args(argv)
    root = repo_root()
    if not args.slug or ".." in args.slug or "/" in args.slug or "\\" in args.slug:
        print("baseline FAILED: slug must not contain a path separator or '..'", file=sys.stderr)
        return 2
    target = root / ".claude" / "prd-flow" / "state" / args.slug
    target.mkdir(parents=True, exist_ok=True)
    if args.bg:
        (target / "baseline.status").write_text("running\n", encoding="utf-8")
        flags = {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        with (target / "baseline.bg.log").open("wb") as out:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), args.slug, "--commit", args.commit, "--wait", str(args.wait)],  # noqa: S603
                             cwd=root, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **flags)
        print(f"baseline {args.slug}: started in the background, status in {target.as_posix()}/baseline.status; gates.sh close checks it")
        return 0
    status = target / "baseline.status"
    try:
        code = execute(args, root, target)
    except BaseException as error:
        status.write_text(f"failed {type(error).__name__}\n", encoding="utf-8")
        raise
    if code not in (0, HUNG) and status.is_file() and status.read_text(encoding="utf-8").startswith("running"):
        status.write_text(f"failed exit {code}\n", encoding="utf-8")
    return code


def execute(args: argparse.Namespace, root: Path, target: Path) -> int:
    commit = git(root, "rev-parse", "--verify", f"{args.commit}^{{commit}}").stdout.strip()
    if not commit:
        print(f"baseline FAILED: {args.commit} is not a commit", file=sys.stderr)
        return 2
    config = load(root)
    tests, commands = config.get("tests", {}), config["commands"]
    command = f"{commands['test']} {commands.get('offline_args', '')} {fast_flags(tests)}"
    base =root / ".claude" / "prd-flow" / "state" / "_baseline"
    cache = base / cache_key(root, commit, command, list(tests.get("baseline_deselect", [])))
    ready = cache / "done"
    lock = base / f"{commit[:12]}.lock"
    (target / "baseline.status").write_text("running\n", encoding="utf-8")
    if ready.is_file():
        return publish(cache, target, f"ok cached {commit[:8]}\n")
    try:
        held = acquire(lock, time.time() + args.wait, ready)
    except TimeoutError as error:
        print(f"baseline FAILED: {error}", file=sys.stderr)
        return 2
    if not held:
        return publish(cache, target, f"ok cached {commit[:8]}\n")
    stop = threading.Event()

    def beat() -> None:
        while not stop.wait(HEARTBEAT_SECONDS):
            lock.touch()

    thread = threading.Thread(target=beat, daemon=True)
    thread.start()
    try:
        if ready.is_file():
            return publish(cache, target, f"ok cached {commit[:8]}\n")
        cache.mkdir(parents=True, exist_ok=True)
        try:
            _, hung = run_suite(root, config, commit, cache)
        except SetupError as error:
            shutil.rmtree(cache, ignore_errors=True)
            print(f"baseline FAILED: {error}", file=sys.stderr)
            return 2
        pattern = re.compile(tests.get("failure_regex", r"^(?:FAILED|ERROR)\s+(\S+)"))
        found = sorted(failures(cache / "run.log", pattern)) if (cache / "run.log").is_file() else []
        (cache / "failures.txt").write_text("".join(f"{f}\n" for f in found), encoding="utf-8")
        if hung:
            idle = tests.get("baseline_idle_seconds", DEFAULT_IDLE_SECONDS)
            publish(cache, target, f"watchdog {commit[:8]}\n")
            shutil.rmtree(cache, ignore_errors=True)
            print(f"baseline INCOMPLETE: no progress for {idle} s, the run was killed; failures so far are recorded, rerun or add the hanging test to tests.baseline_deselect")
            return HUNG
        if not (cache / "run.log").is_file() or not has_summary(cache / "run.log", tests):
            log = (cache / "run.log").as_posix()
            (target / "baseline.status").write_text("failed no summary\n", encoding="utf-8")
            print(f"baseline FAILED: {NO_SUMMARY}, log {log}; nothing was recorded or cached", file=sys.stderr)
            return 2
        ready.write_text(f"{commit}\n", encoding="utf-8")
        return publish(cache, target, f"ok {commit[:8]}\n")
    finally:
        stop.set()
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

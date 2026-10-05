"""Disk and image guards, the sweep of stale test leftovers and docker-clean, driven by scripts/gates.sh.

Every image, container, volume and network the repository creates carries the labels named by the "docker"
section of ai-kit.json: <namespace>.repo=<repo> and <namespace>.purpose=test|dev|spike. Only labelled objects
are ever removed; unlabelled images belong to other projects and are reported, never touched. Without that
section every Docker target is a no-op.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_MIN_FREE_GB = 10.0
DEFAULT_IMAGE_CAP = 8
DEFAULT_IMAGE_CAP_GB = 6.0
DEFAULT_TOTAL_IMAGE_CAP_GB = 20.0
DEFAULT_BUILD_CACHE_MAX_GB = 3
DEFAULT_STALE_MINUTES = 60
DEFAULT_DOCKER_DISK_WARN_GB = 40.0
_UNITS = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
_SIZE = re.compile(r"([\d.]+)\s*([kKMGT]?B)")
_CONTAINER_ROW = '{{.ID}}|{{.Label "com.docker.compose.project"}}|{{.CreatedAt}}'


@dataclass(frozen=True)
class Result:
    code: int
    out: str


@dataclass(frozen=True)
class Labels:
    namespace: str
    repo: str

    @property
    def repo_label(self) -> str:
        return f"{self.namespace}.repo={self.repo}"

    def purpose(self, value: str) -> str:
        return f"{self.namespace}.purpose={value}"


Runner = Callable[[Sequence[str]], Result]


def load_labels(root: Path) -> Labels | None:
    section = json.loads((root / "ai-kit.json").read_text(encoding="utf-8")).get("docker")
    if not section:
        return None
    return Labels(section["label_namespace"], section["repo"])


def run_docker(args: Sequence[str]) -> Result:
    cli = shlex.split(os.environ.get("DOCKER_CLI", "docker"))
    done = subprocess.run([*cli, *args], capture_output=True, text=True, check=False, timeout=600)  # noqa: S603
    return Result(done.returncode, (done.stdout + done.stderr).strip())


def parse_size(text: str) -> int:
    match = _SIZE.search(text)
    if match is None:
        return 0
    return int(float(match.group(1)) * _UNITS[match.group(2).upper()])


def fmt_bytes(count: int) -> str:
    return f"{count / 10**9:.2f} GB" if count >= 10**9 else f"{count / 10**6:.1f} MB"


def free_gb(paths: Sequence[Path], env: dict[str, str]) -> float:
    override = env.get("GATES_FREE_GB_OVERRIDE")
    if override:
        return float(override)
    return min(shutil.disk_usage(path).free for path in paths) / 10**9


def check_disk(env: dict[str, str], paths: Sequence[Path] | None = None) -> int:
    minimum = float(env.get("MIN_FREE_GB", DEFAULT_MIN_FREE_GB))
    watched = paths or [Path.cwd(), Path(tempfile.gettempdir())]
    free = free_gb(watched, env)
    if free < minimum:
        print(
            f"refusing to build or start containers: {free:.1f} GB free, {minimum:g} GB required "
            "(MIN_FREE_GB). Run scripts/gates.sh docker-clean and free space.",
            file=sys.stderr,
        )
        return 1
    print(f"disk ok: {free:.1f} GB free (minimum {minimum:g} GB)")
    return 0


def _sized_rows(text: str) -> list[tuple[str, int]]:
    rows = [line.split("|", 1) for line in text.splitlines() if "|" in line]
    return [(name, parse_size(size)) for name, size in rows]


def labelled_images(labels: Labels, run: Runner) -> list[tuple[str, int]]:
    listing = run(
        ["image", "ls", "--filter", f"label={labels.repo_label}", "--format", "{{.Repository}}:{{.Tag}}|{{.Size}}"]
    )
    if listing.code != 0:
        raise RuntimeError(f"cannot list images: {listing.out}")
    return _sized_rows(listing.out)


def check_total_images(env: dict[str, str], run: Runner = run_docker) -> int:
    cap_bytes = int(float(env.get("TOTAL_IMAGE_CAP_GB", DEFAULT_TOTAL_IMAGE_CAP_GB)) * 10**9)
    listing = run(["image", "ls", "--format", "{{.Repository}}:{{.Tag}}|{{.Size}}"])
    if listing.code != 0:
        print(f"total image size not verified: {listing.out}", file=sys.stderr)
        return 1
    images = sorted(_sized_rows(listing.out), key=lambda row: row[1], reverse=True)
    total = sum(size for _, size in images)
    if total > cap_bytes:
        biggest = "\n".join(f"  {name}  {fmt_bytes(size)}" for name, size in images[:5])
        print(
            f"refusing to build or pull: all images take {fmt_bytes(total)} (cap {cap_bytes / 10**9:g} GB, "
            f"TOTAL_IMAGE_CAP_GB). Remove what no project uses any more; the biggest:\n{biggest}",
            file=sys.stderr,
        )
        return 1
    print(f"total image size ok: {len(images)} images, {fmt_bytes(total)}")
    return 0


def check_image_cap(env: dict[str, str], labels: Labels, run: Runner = run_docker) -> int:
    cap = int(env.get("IMAGE_CAP", DEFAULT_IMAGE_CAP))
    cap_bytes = int(float(env.get("IMAGE_CAP_GB", DEFAULT_IMAGE_CAP_GB)) * 10**9)
    try:
        images = labelled_images(labels, run)
    except RuntimeError as error:
        print(f"image cap not verified: {error}", file=sys.stderr)
        return 1
    total = sum(size for _, size in images)
    if len(images) > cap or total > cap_bytes:
        print(
            f"refusing to build: {len(images)} labelled images, {fmt_bytes(total)} "
            f"(cap {cap} images or {cap_bytes / 10**9:g} GB, IMAGE_CAP / IMAGE_CAP_GB). "
            "Run scripts/gates.sh docker-clean.",
            file=sys.stderr,
        )
        return 1
    print(f"image cap ok: {len(images)} labelled images, {fmt_bytes(total)}")
    return 0


def prune_build_cache(env: dict[str, str], run: Runner = run_docker) -> int:
    limit = f"{env.get('BUILD_CACHE_MAX_GB', DEFAULT_BUILD_CACHE_MAX_GB)}gb"
    pruned = run(["builder", "prune", "--max-used-space", limit, "-f"])
    if pruned.code != 0:
        print(f"build cache prune failed, continuing: {pruned.out[-400:]}", file=sys.stderr)
    else:
        print(pruned.out.splitlines()[-1] if pruned.out else "build cache pruned")
    return 0


def _reclaimed(text: str) -> int:
    match = re.search(r"reclaimed space:\s*(.+)", text, re.IGNORECASE)
    return parse_size(match.group(1)) if match else 0


def _step(name: str, run: Runner, args: Sequence[str], report: list[str], failures: list[str]) -> int:
    result = run(args)
    if result.code != 0:
        failures.append(f"{name}: {result.out[-300:]}")
        report.append(f"{name}: FAILED (continuing)")
        return 0
    freed = _reclaimed(result.out)
    removed = [line for line in result.out.splitlines() if line and not line.lower().startswith(("total", "deleted"))]
    report.append(f"{name}: ok, {len(removed)} removed, {fmt_bytes(freed)} reclaimed")
    return freed


def _docker_time(text: str) -> datetime:
    return datetime.strptime(" ".join(text.split()[:3]), "%Y-%m-%d %H:%M:%S %z")


def _sweep_containers(run: Runner, test: list[str], cutoff: datetime, failures: list[str]) -> int:
    listing = run(["ps", "-a", *test, "--format", _CONTAINER_ROW])
    if listing.code != 0:
        failures.append(f"list containers: {listing.out[-300:]}")
        return 0
    groups: dict[str, list[tuple[str, datetime]]] = defaultdict(list)
    for line in listing.out.splitlines():
        parts = line.split("|")
        if len(parts) == 3:
            container, project, created = parts
            groups[project or f"container {container}"].append((container, _docker_time(created)))
    removed = 0
    for members in groups.values():
        if max(created for _, created in members) > cutoff:
            continue
        ids = [container for container, _ in members]
        removal = run(["rm", "-f", "-v", *ids])
        if removal.code == 0:
            removed += len(ids)
        else:
            failures.append(f"remove containers {' '.join(ids)}: {removal.out[-300:]}")
    return removed


def _sweep_volumes(run: Runner, test: list[str], cutoff: datetime, failures: list[str]) -> int:
    listing = run(["volume", "ls", "-q", "--filter", "dangling=true", *test])
    names = listing.out.split() if listing.code == 0 else []
    if listing.code != 0:
        failures.append(f"list volumes: {listing.out[-300:]}")
    if not names:
        return 0
    inspected = run(["volume", "inspect", "--format", "{{.Name}}|{{.CreatedAt}}", *names])
    removed = 0
    for line in inspected.out.splitlines() if inspected.code == 0 else []:
        name, _, created = line.partition("|")
        if datetime.fromisoformat(created.strip()) > cutoff:
            continue
        removal = run(["volume", "rm", name])
        if removal.code == 0:
            removed += 1
        else:
            failures.append(f"remove volume {name}: {removal.out[-300:]}")
    if inspected.code != 0:
        failures.append(f"inspect volumes: {inspected.out[-300:]}")
    return removed


def sweep(labels: Labels, stale_minutes: int, now: datetime, run: Runner = run_docker) -> int:
    """Remove test containers, volumes and networks of this repo older than stale_minutes: a killed run's leftovers.

    Younger objects may belong to a run still going in another session, so they stay.
    """
    failures: list[str] = []
    cutoff = now - timedelta(minutes=stale_minutes)
    test = ["--filter", f"label={labels.repo_label}", "--filter", f"label={labels.purpose('test')}"]
    containers = _sweep_containers(run, test, cutoff, failures)
    volumes = _sweep_volumes(run, test, cutoff, failures)
    for name, args in (
        ("networks", ["network", "prune", "-f", *test, "--filter", f"until={stale_minutes}m"]),
        ("dangling images", ["image", "prune", "-f", "--filter", f"label={labels.repo_label}"]),
    ):
        result = run(args)
        if result.code != 0:
            failures.append(f"{name}: {result.out[-300:]}")
    print(f"sweep: {containers} containers and {volumes} volumes of test runs older than {stale_minutes} min removed")
    for failure in failures:
        print(f"sweep step failed, continuing: {failure}", file=sys.stderr)
    return 0


def docker_disk_file() -> Path | None:
    candidates = []
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Docker" / "wsl" / "disk" / "docker_data.vhdx")
    if os.environ.get("HOME"):
        mac = Path(os.environ["HOME"]) / "Library" / "Containers" / "com.docker.docker" / "Data" / "vms" / "0"
        candidates.append(mac / "data" / "Docker.raw")
    return next((path for path in candidates if path.is_file()), None)


def check_docker_disk_file(env: dict[str, str], path: Path | None = None) -> int:
    """Warn, never refuse: the Docker Desktop disk file grows with every build and never shrinks by itself."""
    disk = path if path is not None else docker_disk_file()
    if disk is None or not disk.is_file():
        return 0
    size = disk.stat().st_size
    limit = float(env.get("DOCKER_DISK_WARN_GB", DEFAULT_DOCKER_DISK_WARN_GB)) * 10**9
    if size > limit:
        print(
            f"warning: the Docker disk file {disk} takes {fmt_bytes(size)} (DOCKER_DISK_WARN_GB {limit / 10**9:g}). "
            "Space freed inside Docker comes back only after: scripts/gates.sh docker-clean, then quit Docker Desktop; "
            "if the file stays large, as admin with Docker Desktop quit and `wsl --shutdown`: "
            f"Optimize-VHD -Path '{disk}' -Mode Full",
            file=sys.stderr,
        )
    return 0


def _spike_images(labels: Labels, run: Runner, report: list[str], failures: list[str]) -> int:
    listing = run(
        [
            "image",
            "ls",
            "--filter",
            f"label={labels.repo_label}",
            "--filter",
            f"label={labels.purpose('spike')}",
            "--format",
            "{{.ID}}|{{.Size}}",
        ]
    )
    rows = [line.split("|", 1) for line in listing.out.splitlines() if "|" in line] if listing.code == 0 else []
    freed = 0
    for image_id, size in rows:
        removal = run(["rmi", "-f", image_id])
        if removal.code == 0:
            freed += parse_size(size)
        else:
            failures.append(f"spike image {image_id}: {removal.out[-300:]}")
    report.append(f"spike images: {len(rows)} found, {fmt_bytes(freed)} reclaimed")
    return freed


def unlabelled_images(labels: Labels, run: Runner) -> list[str]:
    everything = run(["image", "ls", "--format", "{{.Repository}}:{{.Tag}}|{{.Size}}"])
    mine = {name for name, _ in labelled_images(labels, run)}
    return [row for row in everything.out.splitlines() if "<none>" not in row and row.split("|")[0] not in mine]


def clean(labels: Labels, run: Runner = run_docker, now: datetime | None = None) -> int:
    """Remove every labelled leftover whatever its age: run it when no test of this repo is running."""
    sweep(labels, 0, now or datetime.now(UTC), run)
    report: list[str] = []
    failures: list[str] = []
    label = ["--filter", f"label={labels.repo_label}"]
    total = 0
    total += _step("stopped containers", run, ["container", "prune", "-f", *label], report, failures)
    total += _step("volumes", run, ["volume", "prune", "-f", "-a", *label], report, failures)
    total += _step("networks", run, ["network", "prune", "-f", *label], report, failures)
    total += _step("dangling images", run, ["image", "prune", "-f"], report, failures)
    total += _spike_images(labels, run, report, failures)
    prune_build_cache(dict(os.environ), run)
    print("\n".join(report))
    print(f"total reclaimed (as reported by docker): {fmt_bytes(total)}")
    if failures:
        print("\nerrors seen (the cleanup went on):", file=sys.stderr)
        print("\n".join(f"  {line}" for line in failures), file=sys.stderr)
    others = unlabelled_images(labels, run)
    print(f"\nunlabelled images left alone ({len(others)}), you decide:")
    print("\n".join(f"  {row.replace('|', '  ')}" for row in others))
    return 0


COMMANDS = ["check-disk", "check-image-cap", "check-docker-disk", "prune-cache", "sweep", "clean"]


def main(argv: Sequence[str], root: Path | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=COMMANDS)
    command = parser.parse_args(argv).command
    env = dict(os.environ)
    if command == "check-disk":
        return check_disk(env)
    labels = load_labels(root or Path.cwd())
    if labels is None:
        print(f"{command}: no docker section in ai-kit.json, nothing to check or clean")
        return 0
    if command == "check-image-cap":
        return max(check_image_cap(env, labels), check_total_images(env))
    if command == "check-docker-disk":
        return check_docker_disk_file(env)
    if command == "prune-cache":
        return prune_build_cache(env)
    if command == "sweep":
        return sweep(labels, int(env.get("DOCKER_STALE_MINUTES", DEFAULT_STALE_MINUTES)), datetime.now(UTC))
    clean(labels)
    return check_docker_disk_file(env)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

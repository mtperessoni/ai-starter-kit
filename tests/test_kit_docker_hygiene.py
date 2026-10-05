"""Docker hygiene of the kit: guards refuse early, a sweep removes only stale test leftovers, cleanup survives a failed run."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from test_kit_scripts import BASH, PY, Project, run, write

KIT = Path(__file__).resolve().parents[1] / "kit"
sys.path.insert(0, str(KIT / "scripts"))

import docker_hygiene as dh  # noqa: E402

LABELS = dh.Labels("org.example", "app")
REPO = "label=org.example.repo=app"
TEST = "label=org.example.purpose=test"
NOW = datetime(2026, 10, 4, 16, 0, tzinfo=UTC)


class FakeDocker:
    def __init__(self, replies: dict[str, dh.Result]) -> None:
        self.replies = replies
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args: Sequence[str]) -> dh.Result:
        self.calls.append(tuple(args))
        for prefix, reply in self.replies.items():
            if " ".join(args).startswith(prefix):
                return reply
        return dh.Result(0, "")

    def removed(self) -> list[tuple[str, ...]]:
        return [call for call in self.calls if call[0] in {"rm", "rmi"} or call[:2] == ("volume", "rm")]


def leftovers() -> FakeDocker:
    containers = "\n".join(
        [
            "c1|app-smoke-aaa|2026-10-04 11:00:00 -0300 -03",
            "c2|app-smoke-aaa|2026-10-04 11:05:00 -0300 -03",
            "c3|app-ping-bbb|2026-10-04 12:50:00 -0300 -03",
            "c4||2026-10-04 09:00:00 -0300 -03",
        ]
    )
    return FakeDocker(
        {
            "ps -a": dh.Result(0, containers),
            "volume ls": dh.Result(0, "v-old\nv-new"),
            "volume inspect": dh.Result(0, "v-old|2026-10-04T14:00:00Z\nv-new|2026-10-04T15:30:00Z"),
        }
    )


def quiet(call):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = call()
    return code, out.getvalue(), err.getvalue()


class GuardsTest(unittest.TestCase):
    def test_disk_guard_minimum_defaults_to_ten_and_is_configurable(self) -> None:
        self.assertEqual(quiet(lambda: dh.check_disk({"GATES_FREE_GB_OVERRIDE": "9.9"}))[0], 1)
        self.assertEqual(quiet(lambda: dh.check_disk({"GATES_FREE_GB_OVERRIDE": "10.1"}))[0], 0)
        self.assertEqual(quiet(lambda: dh.check_disk({"GATES_FREE_GB_OVERRIDE": "3", "MIN_FREE_GB": "2"}))[0], 0)

    def test_labelled_image_cap_refuses_over_count_or_size(self) -> None:
        many = FakeDocker({f"image ls --filter {REPO}": dh.Result(0, "\n".join(f"x{n}:local|10MB" for n in range(9)))})
        big = FakeDocker({f"image ls --filter {REPO}": dh.Result(0, "a:local|4GB\nb:local|3GB")})
        self.assertEqual(quiet(lambda: dh.check_image_cap({}, LABELS, many))[0], 1)
        self.assertEqual(quiet(lambda: dh.check_image_cap({}, LABELS, big))[0], 1)
        self.assertEqual(quiet(lambda: dh.check_image_cap({"IMAGE_CAP_GB": "10"}, LABELS, big))[0], 0)

    def test_total_image_cap_counts_every_project_and_names_the_biggest(self) -> None:
        docker = FakeDocker({"image ls --format": dh.Result(0, "localstack:latest|9GB\nclickhouse:25|8GB\nx:1|4GB")})
        code, _, err = quiet(lambda: dh.check_total_images({}, docker))
        self.assertEqual(code, 1)
        self.assertIn("TOTAL_IMAGE_CAP_GB", err)
        self.assertLess(err.index("localstack"), err.index("clickhouse"))
        self.assertEqual(quiet(lambda: dh.check_total_images({"TOTAL_IMAGE_CAP_GB": "30"}, docker))[0], 0)

    def test_build_cache_is_bounded_by_size_with_no_age_window_and_never_fails(self) -> None:
        docker = FakeDocker({"builder prune": dh.Result(1, "lstat snapshots/4307/fs: no such file")})
        self.assertEqual(quiet(lambda: dh.prune_build_cache({}, docker))[0], 0)
        self.assertEqual(docker.calls, [("builder", "prune", "--max-used-space", "3gb", "-f")])

    def test_docker_disk_file_over_the_threshold_warns_and_never_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            disk = Path(tmp) / "docker_data.vhdx"
            disk.write_bytes(b"x" * 2048)
            code, _, err = quiet(lambda: dh.check_docker_disk_file({"DOCKER_DISK_WARN_GB": "0.000001"}, disk))
            self.assertEqual(code, 0)
            self.assertIn("Optimize-VHD", err)
            self.assertEqual(quiet(lambda: dh.check_docker_disk_file({}, disk)), (0, "", ""))


class SweepTest(unittest.TestCase):
    def test_stale_test_stacks_go_and_live_ones_stay(self) -> None:
        docker = leftovers()
        quiet(lambda: dh.sweep(LABELS, 60, NOW, docker))
        removed = docker.removed()
        self.assertIn(("rm", "-f", "-v", "c1", "c2"), removed)
        self.assertIn(("rm", "-f", "-v", "c4"), removed)
        self.assertFalse(any("c3" in call for call in removed))
        self.assertIn(("volume", "rm", "v-old"), removed)
        self.assertFalse(any("v-new" in call for call in removed))

    def test_every_listing_and_prune_is_filtered_to_this_repo_and_tests(self) -> None:
        docker = leftovers()
        quiet(lambda: dh.sweep(LABELS, 60, NOW, docker))
        for call in docker.calls:
            if call[:2] in {("ps", "-a"), ("volume", "ls"), ("network", "prune")}:
                self.assertIn(REPO, call)
                self.assertIn(TEST, call)
            if call[:2] == ("image", "prune"):
                self.assertIn(REPO, call)

    def test_a_failing_step_is_reported_and_the_sweep_goes_on(self) -> None:
        docker = FakeDocker({"ps -a": dh.Result(1, "daemon down")})
        code, _, err = quiet(lambda: dh.sweep(LABELS, 60, NOW, docker))
        self.assertEqual(code, 0)
        self.assertIn("daemon down", err)
        self.assertTrue(any(call[:2] == ("network", "prune") for call in docker.calls))

    def test_clean_removes_test_leftovers_of_any_age(self) -> None:
        docker = leftovers()
        quiet(lambda: dh.clean(LABELS, docker, NOW))
        self.assertIn(("rm", "-f", "-v", "c3"), docker.removed())
        self.assertIn(("volume", "rm", "v-new"), docker.removed())


FAKE_DOCKER = """\
import os, sys
with open(os.environ["FAKE_DOCKER_LOG"], "a", encoding="utf-8") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
sys.exit(1 if " ".join(sys.argv[1:]).startswith(os.environ.get("FAKE_DOCKER_FAIL", "never")) else 0)
"""


@unittest.skipUnless(BASH, "bash not available")
class GatesDockerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def _gates(self, target: str, fail: str = "never") -> tuple[int, list[str]]:
        fake = write(self.p.root, "fake_docker.py", FAKE_DOCKER)
        log = self.p.root / "docker.log"
        env = {
            "GATES_FREE_GB_OVERRIDE": "50",
            "DOCKER_CLI": f"{Path(PY).as_posix()} {fake.as_posix()}",
            "FAKE_DOCKER_LOG": str(log),
            "FAKE_DOCKER_FAIL": fail,
            "TMPDIR": str(self.p.root),
        }
        saved = {key: os.environ.get(key) for key in env}
        os.environ.update(env)
        try:
            result = run(self.p.root, BASH, "scripts/gates.sh", target)
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        return result.returncode, calls

    def _with_docker_section(self) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["docker"] = {"label_namespace": "org.example", "repo": "app"}
        config_path.write_text(json.dumps(config), encoding="utf-8")

    def test_build_sweeps_and_bounds_the_cache_even_when_the_build_fails(self) -> None:
        self._with_docker_section()
        for fail in ("never", "compose build"):
            code, calls = self._gates("build", fail)
            self.assertEqual(code != 0, fail != "never")
            built = next(n for n, call in enumerate(calls) if call.startswith("compose build"))
            after = calls[built + 1 :]
            self.assertTrue(any(call.startswith("ps -a") and TEST in call for call in after), calls)
            self.assertTrue(any(call.startswith("builder prune --max-used-space") for call in after), calls)
            (self.p.root / "docker.log").unlink()

    def test_without_a_docker_section_the_docker_targets_touch_nothing(self) -> None:
        code, calls = self._gates("sweep")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

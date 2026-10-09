import io
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kit" / "scripts"))

import cleanup  # noqa: E402

DAY = 86400.0


def age(path, days):
    when = time.time() - days * DAY
    os.utime(path, (when, when))


def put(path, text="x", days=0.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    age(path, days)
    return path


def reaper(survivors=()):
    def fake(argv):
        print("reaped: 0")
        if survivors:
            print(f"left: {len(survivors)}")
            for pid in survivors:
                print(f"  {pid} python -")
            return 1
        print("left: 0")
        return 0

    return fake


class CleanupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / "repo"
        self.outputs = base / "claude"
        self.state = self.root / ".claude" / "prd-flow" / "state"
        self.runs = self.root / ".ai-kit" / "runs"
        self.root.mkdir()

    def run_cleanup(self, argv=(), survivors=()):
        out = io.StringIO()
        with redirect_stdout(out):
            code = cleanup.main(list(argv), root=self.root, outputs_root=self.outputs, reap_main=reaper(survivors))
        return code, out.getvalue()

    def test_loose_files_in_runs_go_but_markers_and_context_folders_stay(self):
        put(self.runs / "stray.json")
        put(self.runs / "current", "slug\n")
        put(self.runs / ".branch", "main")
        put(self.runs / "ctx" / "events.jsonl")
        code, out = self.run_cleanup()
        self.assertFalse((self.runs / "stray.json").exists())
        self.assertTrue((self.runs / "current").exists())
        self.assertTrue((self.runs / ".branch").exists())
        self.assertTrue((self.runs / "ctx" / "events.jsonl").exists())
        self.assertEqual(code, 0)
        self.assertTrue(out.rstrip().endswith("left: 0"))

    def test_state_folders_untouched_for_7_days_move_to_stale_except_underscored_and_the_slug(self):
        put(self.state / "old" / "state.md", days=8)
        put(self.state / "fresh" / "state.md", days=1)
        put(self.state / "mine" / "state.md", days=30)
        put(self.state / "_close" / "x.log", days=30)
        self.run_cleanup(["mine"])
        self.assertTrue((self.state / "_stale" / "old" / "state.md").exists())
        self.assertFalse((self.state / "old").exists())
        self.assertTrue((self.state / "fresh" / "state.md").exists())
        self.assertTrue((self.state / "mine" / "state.md").exists())
        self.assertTrue((self.state / "_close" / "x.log").exists())

    def test_a_folder_with_a_recent_file_inside_is_not_stale(self):
        put(self.state / "busy" / "old.md", days=20)
        put(self.state / "busy" / "new.md", days=1)
        self.run_cleanup()
        self.assertTrue((self.state / "busy" / "new.md").exists())

    def test_stale_entries_older_than_14_days_are_deleted(self):
        put(self.state / "_stale" / "gone" / "a.md", days=15)
        age(self.state / "_stale" / "gone", 15)
        put(self.state / "_stale" / "kept" / "a.md", days=10)
        self.run_cleanup()
        self.assertFalse((self.state / "_stale" / "gone").exists())
        self.assertTrue((self.state / "_stale" / "kept").exists())

    def test_tests_and_gate_caches_older_than_3_days_are_deleted(self):
        put(self.state / "_tests" / "old.log", days=4)
        put(self.state / "_tests" / "new.log", days=1)
        put(self.state / "_gate" / "old.json", days=4)
        self.run_cleanup()
        self.assertFalse((self.state / "_tests" / "old.log").exists())
        self.assertTrue((self.state / "_tests" / "new.log").exists())
        self.assertFalse((self.state / "_gate" / "old.json").exists())

    def test_session_end_only_reaps_and_cleans_task_outputs(self):
        put(self.runs / "stray.json")
        put(self.state / "old" / "state.md", days=30)
        slug_dir = self.outputs / cleanup.project_slug(self.root) / "sess" / "tasks"
        put(slug_dir / "a.output", days=1)
        self.run_cleanup(["--session-end"])
        self.assertTrue((self.runs / "stray.json").exists())
        self.assertTrue((self.state / "old" / "state.md").exists())
        self.assertFalse((slug_dir / "a.output").exists())

    def test_task_outputs_of_this_project_that_are_idle_are_deleted_and_a_live_one_is_kept(self):
        slug_dir = self.outputs / cleanup.project_slug(self.root) / "sess" / "tasks"
        put(slug_dir / "idle.output", days=0.1)
        put(slug_dir / "live.output", days=0.0)
        other = put(self.outputs / "other-project" / "s" / "tasks" / "o.output", days=1)
        self.run_cleanup()
        self.assertFalse((slug_dir / "idle.output").exists())
        self.assertTrue((slug_dir / "live.output").exists())
        self.assertTrue(other.exists())

    def test_cleanup_never_touches_other_slugs_the_parent_slug_a_young_output_or_a_huge_foreign_one(self):
        mine = self.outputs / cleanup.project_slug(self.root) / "sess" / "tasks"
        young = put(mine / "young.output", days=1 / 24)
        parent = put(self.outputs / cleanup.project_slug(self.root.parent) / "s" / "tasks" / "p.output", days=3)
        foreign = put(self.outputs / "other" / "s" / "tasks" / "big.output", days=3)
        self.run_cleanup()
        self.assertTrue(young.exists())
        self.assertTrue(parent.exists())
        self.assertTrue(foreign.exists())

    def test_dry_run_deletes_and_moves_nothing(self):
        put(self.runs / "stray.json")
        put(self.state / "old" / "state.md", days=30)
        put(self.state / "_tests" / "old.log", days=9)
        code, out = self.run_cleanup(["--dry-run"])
        self.assertTrue((self.runs / "stray.json").exists())
        self.assertTrue((self.state / "old" / "state.md").exists())
        self.assertTrue((self.state / "_tests" / "old.log").exists())
        self.assertEqual(code, 0)

    def test_a_survivor_is_listed_and_exits_1_within_8_lines(self):
        code, out = self.run_cleanup(survivors=[41, 42])
        self.assertEqual(code, 1)
        self.assertIn("left: 2", out)
        self.assertIn("41", out)
        self.assertLessEqual(len(out.strip().splitlines()), 8)

    def test_a_symlink_or_path_outside_the_repo_is_never_followed(self):
        outside = Path(self.tmp.name) / "outside"
        put(outside / "keep.txt", days=30)
        self.state.mkdir(parents=True)
        try:
            os.symlink(outside, self.state / "link", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("no symlinks")
        self.run_cleanup()
        self.assertTrue((outside / "keep.txt").exists())

    def test_output_is_at_most_8_lines_and_ends_with_left_0(self):
        for n in range(5):
            put(self.state / f"old{n}" / "state.md", days=30)
        code, out = self.run_cleanup()
        lines = out.strip().splitlines()
        self.assertLessEqual(len(lines), 8)
        self.assertEqual(lines[-1], "left: 0")


if __name__ == "__main__":
    unittest.main()

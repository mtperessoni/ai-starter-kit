"""Tests of eval/regrade.py: a two-phase run is regraded on both of its transcripts, as eval/run.py grades it."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import regrade  # noqa: E402

CONFIG = EVAL / "arms-short.json"


class TwoPhaseRegradeTest(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp())
        self.results, self.projects = root / "results", root / "projects"
        self.results.mkdir()
        self.projects.mkdir()

    def add_run(self, name, phase2):
        (self.projects / name).mkdir()
        (self.results / f"{name}.run.json").write_text(json.dumps(
            {"name": name, "arm": "FLOW-FAST", "scenario": "S5", "rep": 1, "status": "ok",
             "started_at": 0, "runner_wall_min": 14.7}), encoding="utf-8")
        (self.results / f"{name}.jsonl").write_text("{}\n", encoding="utf-8")
        if phase2:
            (self.results / f"{name}.p2.jsonl").write_text("{}\n", encoding="utf-8")

    def regrade(self):
        seen = {}

        def fake_grade(project, scenario, arm, transcript=None, **_):
            seen[Path(project).name] = transcript
            return {"wall_min": 1.0}

        with mock.patch.object(regrade.grade, "grade", side_effect=fake_grade), \
                mock.patch.object(regrade.grade, "seed_commit", return_value="seed"):
            done, skipped = regrade.regrade(self.results, CONFIG, self.projects)
        return done, skipped, seen

    def test_two_phase_run_is_graded_on_both_transcripts(self):
        self.add_run("FLOW-FAST-S5-r1", phase2=True)
        done, skipped, seen = self.regrade()
        self.assertEqual(done, ["FLOW-FAST-S5-r1"])
        self.assertEqual(skipped, [])
        self.assertEqual([Path(t).name for t in seen["FLOW-FAST-S5-r1"]],
                         ["FLOW-FAST-S5-r1.jsonl", "FLOW-FAST-S5-r1.p2.jsonl"])

    def test_phase2_transcript_is_not_a_run_of_its_own(self):
        self.add_run("FLOW-FAST-S5-r1", phase2=True)
        self.regrade()
        self.assertFalse((self.results / "FLOW-FAST-S5-r1.p2.metrics.json").exists())

    def test_single_phase_run_keeps_one_transcript(self):
        self.add_run("GATE-S5-r1", phase2=False)
        done, skipped, seen = self.regrade()
        self.assertEqual((done, skipped), (["GATE-S5-r1"], []))
        self.assertEqual(Path(seen["GATE-S5-r1"]).name, "GATE-S5-r1.jsonl")


class FindProjectTest(unittest.TestCase):
    def test_picks_the_build_of_the_run_not_a_later_round(self):
        import datetime
        root = Path(tempfile.mkdtemp()) / "ai-kit-eval"
        for stamp in ("20261008-091556", "20261008-094815", "20261008-100411"):
            (root / stamp / "FLOW-FAST-S5-r1").mkdir(parents=True)
        started = datetime.datetime(2026, 10, 8, 9, 15, 59).timestamp()
        with mock.patch.object(regrade.tempfile, "gettempdir", return_value=str(root.parent)):
            found = regrade.find_project("FLOW-FAST-S5-r1", started_at=started)
        self.assertEqual(found.parent.name, "20261008-091556")


if __name__ == "__main__":
    unittest.main()

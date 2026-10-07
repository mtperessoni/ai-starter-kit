"""Tests of the K-91 additions to eval/judge.py with an injected runner."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import judge  # noqa: E402


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false",
                    *args], cwd=root, check=True, capture_output=True)


class JudgeK91Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project, self.scenario = root / "p", root / "s"
        (self.project / "docs" / "prd").mkdir(parents=True)
        self.scenario.mkdir()
        (self.project / "docs" / "prd" / "01.md").write_text("| PRC-03 | cap 30% | x | code |\n", encoding="utf-8")
        git(self.project, "init", "-q")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-q", "-m", "seed")
        self.seed = judge.grade.seed_commit(self.project)
        (self.scenario / "decisions.md").write_text("dec", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def expect(self, **kw):
        exp = {"prd_facts": [{"id": "f1", "fact": "x"}], **kw}
        (self.scenario / "expected.json").write_text(json.dumps(exp), encoding="utf-8")

    def ask(self, answer):
        def runner(cmd, stdin, cwd):
            self.prompt = stdin
            return 0, json.dumps({"result": json.dumps(answer), "total_cost_usd": 0.1})
        return judge.judge(self.project, self.scenario, self.seed, runner=runner)

    def test_conflict_section_and_contradiction_count(self):
        self.expect(conflict_ids=["PRC-03", "PRC-04"])
        r = self.ask({"facts": [{"id": "f1", "verdict": "stated"}], "contradictions_left": ["PRC-03", "ZZZ-1"]})
        self.assertIn("## Conflict check", self.prompt)
        self.assertIn("| PRC-03 | cap 30%", self.prompt)
        self.assertEqual(r["contradiction_left"], 1)
        self.assertIsNone(r["gap_recorded"])

    def test_no_contradiction_reported_is_zero(self):
        self.expect(conflict_ids=["PRC-03"])
        self.assertEqual(self.ask({"facts": []})["contradiction_left"], 0)

    def test_gap_section_and_flag(self):
        self.expect(gap_topic="what happens to orders already paid")
        r = self.ask({"facts": [], "gap_recorded": True})
        self.assertIn("## Open dimension", self.prompt)
        self.assertIn("orders already paid", self.prompt)
        self.assertTrue(r["gap_recorded"])
        self.assertIsNone(r["contradiction_left"])
        self.assertFalse(self.ask({"facts": [], "gap_recorded": "yes"})["gap_recorded"])

    def test_plain_scenario_leaves_both_none_and_adds_no_section(self):
        self.expect()
        r = self.ask({"facts": []})
        self.assertNotIn("## Conflict check", self.prompt)
        self.assertNotIn("## Open dimension", self.prompt)
        self.assertEqual((r["contradiction_left"], r["gap_recorded"]), (None, None))

    def test_no_judge_defaults_carry_the_keys(self):
        self.assertIn("contradiction_left", judge.NO_JUDGE)
        self.assertIn("gap_recorded", judge.NO_JUDGE)


if __name__ == "__main__":
    unittest.main()

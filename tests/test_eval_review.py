"""Tests of eval/review.py with a fake runner; claude is never called."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import review  # noqa: E402


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false",
                    *args], cwd=root, check=True, capture_output=True)


class Fake:
    def __init__(self, envelope=None, code=0, raw=None):
        self.out = raw if raw is not None else json.dumps(envelope)
        self.code, self.calls = code, []

    def __call__(self, cmd, stdin, cwd):
        self.calls.append((cmd, stdin, cwd))
        return self.code, self.out


FINDINGS = {"findings": [
    {"severity": "critical", "kind": "bug", "file": "src/a.py", "summary": "x"},
    {"severity": "high", "kind": "rule_mismatch", "file": "src/a.py", "summary": "y"},
    {"severity": "high", "kind": "test_gap", "file": "tests/t.py", "summary": "z"},
    {"severity": "low", "kind": "maintainability", "file": "src/b.py", "summary": "w"},
    {"severity": "weird", "kind": "bug"}, "junk"], "approve": False}


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name) / "proj"
        self.p.mkdir()
        git(self.p, "init", "-q")
        write(self.p, "docs/prd/01.md", "| PRC-01 | rule one |\n")
        write(self.p, "docs/prd/02.md", "| PRC-02 | rule two |\n")
        write(self.p, "src/a.py", "x = 1\n")
        git(self.p, "add", "-A")
        git(self.p, "commit", "-q", "-m", "seed")
        self.seed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.p, capture_output=True,
                                   text=True).stdout.strip()
        self.env = mock.patch.dict(os.environ, {"EVAL_NO_REVIEW": "", "EVAL_NO_JUDGE": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def change(self, prd=True):
        write(self.p, "src/a.py", "x = 2\n")
        write(self.p, "tests/test_a.py", "def test_a():\n    assert True\n")
        write(self.p, "specs/001/plan.md", "SECRETPLAN\n")
        write(self.p, "CLAUDE.md", "SECRETCLAUDE\n")
        write(self.p, "src/feat/CLAUDE.md", "SECRETMAP\n")
        write(self.p, ".claude/x.md", "SECRETKIT\n")
        if prd:
            write(self.p, "docs/prd/01.md", "| PRC-01 | rule one changed |\n")
        git(self.p, "add", "-A")
        git(self.p, "commit", "-q", "-m", "change")

    def run_review(self, fake):
        return review.review(self.p, self.tmp.name, self.seed, runner=fake)

    def test_prompt_has_rubric_touched_prd_and_code_diff_only(self):
        self.change()
        prompt = review.build_prompt(self.p, self.seed)
        self.assertIn("senior code reviewer", prompt)
        for sev in review.SEVERITIES:
            self.assertIn(f"- {sev}:", prompt)
        self.assertIn("rule one changed", prompt)
        self.assertNotIn("rule two", prompt)
        self.assertIn("+x = 2", prompt)
        self.assertIn("test_a", prompt)
        for secret in ("SECRETPLAN", "SECRETCLAUDE", "SECRETMAP", "SECRETKIT"):
            self.assertNotIn(secret, prompt)

    def test_unchanged_prd_uses_whole_tree(self):
        self.change(prd=False)
        prompt = review.build_prompt(self.p, self.seed)
        self.assertIn("rule one", prompt)
        self.assertIn("rule two", prompt)

    def test_caps(self):
        write(self.p, "docs/prd/03.md", "p" * 100_000)
        write(self.p, "src/big.py", "\n".join(f"v{i} = {i}" for i in range(40_000)) + "\n")
        git(self.p, "add", "-A")
        git(self.p, "commit", "-q", "-m", "big")
        self.assertLessEqual(len(review.touched_prd(self.p, self.seed)), review.MAX_PRD)
        self.assertLessEqual(len(review.code_diff(self.p, self.seed)), review.MAX_DIFF)

    def test_result_counts(self):
        self.change()
        fake = Fake({"result": json.dumps(FINDINGS), "total_cost_usd": 0.3})
        r = self.run_review(fake)
        self.assertEqual(r["blind_findings"], {"critical": 1, "high": 2, "medium": 0, "low": 1})
        self.assertEqual(r["blind_findings_total"], 4)
        self.assertEqual(r["blind_bugs"], 2)
        self.assertIs(r["blind_approve"], False)
        self.assertEqual(len(r["blind_detail"]), 4)
        self.assertEqual(r["review_cost_usd"], 0.3)
        cmd, stdin, cwd = fake.calls[0]
        self.assertEqual(cmd[:4], ["claude", "-p", "--model", "sonnet"])
        self.assertIn("--max-budget-usd", cmd)
        self.assertIn("2", cmd)
        self.assertIn("PRD sections", stdin)

    def test_fenced_json_and_clean_approve(self):
        self.change()
        text = "```json\n" + json.dumps({"findings": [], "approve": True}) + "\n```"
        r = self.run_review(Fake({"result": text}))
        self.assertEqual((r["blind_findings_total"], r["blind_bugs"], r["blind_approve"]), (0, 0, True))

    def test_skip_flags(self):
        self.change()
        for var in ("EVAL_NO_REVIEW", "EVAL_NO_JUDGE"):
            with mock.patch.dict(os.environ, {var: "1"}):
                fake = Fake({"result": "{}"})
                r = self.run_review(fake)
                self.assertEqual(fake.calls, [])
                self.assertIsNone(r["blind_bugs"])
                self.assertIsNone(r["review_cost_usd"])

    def test_failures_return_none_values(self):
        self.change()
        for fake in (Fake(raw="not json"), Fake({"result": "no json here"}),
                     Fake({"result": "{}", "total_cost_usd": 0.1}, code=1)):
            r = self.run_review(fake)
            self.assertIsNone(r["blind_bugs"])
            self.assertIsNone(r["blind_findings"])
        cost = self.run_review(Fake({"result": "x", "total_cost_usd": 0.2}))["review_cost_usd"]
        self.assertEqual(cost, 0.2)


if __name__ == "__main__":
    unittest.main()

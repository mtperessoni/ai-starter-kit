"""Tests of eval/grade.py, eval/report.py and the pure parts of eval/run.py on a tiny fake project."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import grade  # noqa: E402
import report  # noqa: E402
import run  # noqa: E402

PRD_SEED = "| ID | Rule | Source | Change via |\n|---|---|---|---|\n| PRC-01 | VIP 15% | src/mod.py | code |\n"
PRD_NEW = PRD_SEED + "| PRC-02 | cap 20% | src/mod.py | planned |\n\n## Planned\n\nFR-001 the cap of 20% applies\n"


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode())
    return p


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false",
                    *args], cwd=root, check=True, capture_output=True)


def make_project(root):
    git(root, "init", "-q")
    write(root, "docs/prd/01.md", PRD_SEED)
    write(root, "src/mod.py", "def f():\n    return 1\n")
    write(root, "tests/test_mod.py", "from mod import f\n\n\ndef test_f():  # PRC-01\n    assert f() == 1\n")
    write(root, ".claude/skills/prd-gate/scripts/gate.py", "import sys\nsys.exit(0)\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "chore: seed")
    write(root, "docs/prd/01.md", PRD_NEW)
    git(root, "commit", "-q", "-am", "docs: cap")
    write(root, "src/mod.py", "def f():\n    return 1\n\n\ndef g():\n    return 2\n")
    git(root, "commit", "-q", "-am", "feat: g")
    write(root, "NOTES.md", "the cap of 20% lives here\n")
    write(root, "src/other.py", "# cap of 20% is ignored under src\n")


def make_scenario(root, case="C5"):
    write(root, "request.md", "req")
    write(root, "decisions.md", "dec")
    write(root, "hidden/test_h.py",
          "from mod import f\n\n\ndef test_a():\n    assert f() == 1\n\n\ndef test_b():\n    assert f() == 2\n")
    exp = {"case": case, "size": "S", "rule_ids": ["PRC-01", "PRC-02"],
           "prd_patterns": ["PRC-02", r"cap 20%"], "dup_phrases": [r"cap of 20%"]}
    write(root, "expected.json", json.dumps(exp))


class SeedDeltaTest(unittest.TestCase):
    """Text already present at the seed (spec-kit templates, existing tests) is not credited to the run."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        write(self.root, "docs/prd/01.md", PRD_SEED)
        write(self.root, ".specify/templates/spec.md", "FR-001 template line\nthe cap of 20% example\n")
        write(self.root, "tests/test_old.py", "def test_old():  # PRC-01\n    pass\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "chore: seed")
        self.seed = grade.seed_commit(self.root)
        write(self.root, "changes/001-cap/brief.md", "FR-002 new\nthe cap of 20% again\n")
        write(self.root, "docs/trd/pricing.md", "# Pricing\n\n## Planned (cap, b)\n")
        write(self.root, "tests/test_new.py", "def test_new():  # PRC-02\n    pass\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "work")

    def tearDown(self):
        self.tmp.cleanup()

    def test_fr_lines_and_dup_count_exclude_seed_text(self):
        files = grade.project_files(self.root)
        self.assertEqual(grade.fr_lines(self.root, files, self.seed), 1)
        self.assertEqual(grade.dup_count(self.root, files, [r"cap of 20%"], self.seed), 1)

    def test_planned_left_counts_trd_planned_sections(self):
        self.assertEqual(grade.planned_left(self.root), 1)

    def test_ids_in_tests_counts_only_tests_changed_since_seed(self):
        files = grade.project_files(self.root)
        self.assertEqual(grade.ids_in_tests(self.root, files, ["PRC-01", "PRC-02"], self.seed), 0.5)


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "proj"
        self.scenario = Path(self.tmp.name) / "scn"
        self.project.mkdir()
        make_project(self.project)
        make_scenario(self.scenario)

    def tearDown(self):
        self.tmp.cleanup()

    def status(self):
        return subprocess.run(["git", "status", "--porcelain"], cwd=self.project,
                              capture_output=True, text=True).stdout

    def test_metrics(self):
        before = self.status()
        m = grade.grade(self.project, self.scenario)
        self.assertEqual(self.status(), before)
        self.assertFalse((self.project / "tests" / "hidden").exists())
        self.assertEqual((m["hidden_passed"], m["hidden_total"], m["hidden_pass"]), (1, 2, 0.5))
        self.assertTrue(m["suite_green"])
        self.assertTrue(m["gate_ok"])
        self.assertTrue(m["prd_ok"])
        self.assertEqual(m["ids_in_tests"], 0.0)
        self.assertTrue(m["docs_first"])
        self.assertEqual(m["planned_left"], 2)
        self.assertEqual(m["dup_count"], 1)
        self.assertEqual(m["fr_lines"], 1)
        self.assertEqual(m["doc_bytes"], len(PRD_NEW) - len(PRD_SEED))
        self.assertEqual(m["commits_after_seed"], 2)
        self.assertFalse(m["completed"])

    def test_docs_first_false_and_none(self):
        git(self.project, "reset", "-q", "--hard", "HEAD~2")
        write(self.project, "src/mod.py", "def f():\n    return 1\n# x\n")
        git(self.project, "commit", "-q", "-am", "feat: first")
        write(self.project, "docs/prd/01.md", PRD_NEW)
        git(self.project, "commit", "-q", "-am", "docs: later")
        self.assertFalse(grade.grade(self.project, self.scenario)["docs_first"])
        write(self.scenario, "expected.json", json.dumps({"case": "C3"}))
        self.assertIsNone(grade.grade(self.project, self.scenario)["docs_first"])

    def test_claude_json(self):
        cj = Path(self.tmp.name) / "c.json"
        cj.write_text(json.dumps({"total_cost_usd": 1.5, "duration_ms": 120000, "num_turns": 7,
                                  "usage": {"input_tokens": 10, "output_tokens": 20,
                                            "cache_read_input_tokens": 30,
                                            "cache_creation_input_tokens": 40}}))
        m = grade.grade(self.project, self.scenario, cj)
        self.assertEqual((m["cost_usd"], m["duration_min"], m["turns"]), (1.5, 2.0, 7))
        self.assertEqual(m["tokens_total"], 100)
        self.assertTrue(m["completed"])

    def test_cost_tolerates_missing_keys(self):
        self.assertIsNone(grade.cost_metrics({})["cost_usd"])
        mu = {"modelUsage": {"m": {"inputTokens": 5, "outputTokens": 6}}}
        self.assertEqual(grade.cost_metrics(mu)["tokens_total"], 11)
        self.assertIsNone(grade.cost_metrics(None)["turns"])


def metrics(**kw):
    base = {"hidden_passed": 4, "hidden_total": 4, "prd_ok": True, "gate_ok": True, "dup_count": 2,
            "cost_usd": 10.0, "duration_min": 20.0, "completed": True}
    return {**base, **kw}


class DecisionRuleTest(unittest.TestCase):
    def verdicts(self, a, b):
        data = {"A": {"S1": a}, "B": {"S1": b}}
        return {r: ok for r, ok, _ in report.evaluate(data)}

    def test_all_pass(self):
        v = self.verdicts(metrics(), metrics(cost_usd=10.9, duration_min=21.9))
        self.assertTrue(all(v.values()), v)

    def test_each_failure(self):
        fails = {
            "hidden_pass": metrics(hidden_passed=3),
            "prd_ok": metrics(prd_ok=False),
            "gate_ok": metrics(gate_ok=False),
            "dup_count": metrics(dup_count=3),
            "cost_usd": metrics(cost_usd=11.1),
            "duration_min": metrics(duration_min=22.1),
        }
        for key, b in fails.items():
            v = self.verdicts(metrics(), b)
            failed = [r for r, ok in v.items() if not ok]
            self.assertEqual(len(failed), 1, (key, v))
            self.assertIn(key, failed[0])

    def test_report_file(self):
        with tempfile.TemporaryDirectory() as d:
            for arm in "AB":
                (Path(d) / f"{arm}-S1.metrics.json").write_text(json.dumps(metrics(status="ok")))
            text = report.write_report(d).read_text(encoding="utf-8")
        for needle in ("## Scenario S1", "## Totals", "PASS: gate_ok", "one repetition", "Within 10%"):
            self.assertIn(needle, text)


class RunTest(unittest.TestCase):
    def test_command(self):
        cmd = run.build_command(12, "claude")
        self.assertEqual(cmd[:4], ["claude", "-p", "--output-format", "json"])
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertEqual(cmd[-2:], ["--max-budget-usd", "12"])

    def test_prompt_and_build_args(self):
        self.assertEqual(run.render_prompt("R:{request} D:{decisions}", " a ", "b\n"), "R:a D:b")
        self.assertIn("--spec-kit", run.build_args("A", "out"))
        self.assertNotIn("--spec-kit", run.build_args("B", "out"))
        self.assertEqual(run.build_args("A", "out")[2:4], ["--ref", "main"])


if __name__ == "__main__":
    unittest.main()

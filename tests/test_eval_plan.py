"""Tests of eval/plan_fidelity.py and eval/judge.py (the judge runs through a fake runner)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import judge  # noqa: E402
import plan_fidelity as pf  # noqa: E402

TASKS_MD = """# Tasks
## Phase 1
- [ ] T001 Create project structure per implementation plan
- [ ] T002 [P] Configure linting in pyproject.toml
- [X] T003 [P] [US1] Implement cap in src/orders/features/pricing/discount_calculator.py
- [ ] T004 [US1] Add test in `src/orders/features/pricing/tests/test_cap.py`, then docs
- [ ] T005 [US1] Placeholder in src/[location]/[file].py
"""

PLAN_MD = """# Plan

## Constitution check
| III | ok |

### T01 · Cap
Contract (literal):
| PRC-03 | ... |
Owns: src/orders/features/pricing/discount_calculator.py, src/orders/features/pricing/tests/test_cap.py
Depends on: none

### T02 · Docs
Owns: docs/trd/pricing.md

### T03 · Promote
- PRD: old text to the CHANGELOG
"""


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root,
                   check=True, capture_output=True)


class ParseTest(unittest.TestCase):
    def test_owns_line_with_backticks_annotations_and_folders(self):
        """The planner writes `path` (new) items; folders own every file under them."""
        text = ("### T01 · Credit\nOwns: `src/orders/features/store_credit/` (new), "
                "`docs/trd/store_credit.md` (new), `src/orders/features/checkout/confirmation.py` (new)\n")
        files = pf.parse_plan_md(text)[0]["files"]
        self.assertEqual(files, ["src/orders/features/store_credit/", "docs/trd/store_credit.md",
                                 "src/orders/features/checkout/confirmation.py"])
        cov, drift = pf.coverage_and_drift(
            pf.parse_plan_md(text), ["src/orders/features/store_credit/credit_application.py"],
            ["src/orders/features/store_credit/credit_application.py"])
        self.assertEqual((cov, drift), (1.0, 0.0))

    def test_docs_only_task_is_covered_by_any_commit(self):
        tasks = [{"id": "T01", "files": ["src/a.py"]}, {"id": "T02", "files": ["changes/"]}]
        cov, _ = pf.coverage_and_drift(tasks, {"src/a.py"}, ["src/a.py"],
                                       all_changed={"src/a.py", "changes/archive/001-x/plan.md"})
        self.assertEqual(cov, 1.0)

    def test_tasks_md(self):
        tasks = pf.parse_tasks_md(TASKS_MD)
        self.assertEqual([t["id"] for t in tasks], ["T001", "T002", "T003", "T004", "T005"])
        self.assertEqual(tasks[0]["files"], [])
        self.assertEqual(tasks[1]["files"], ["pyproject.toml"])
        self.assertEqual(tasks[2]["files"], ["src/orders/features/pricing/discount_calculator.py"])
        self.assertEqual(tasks[3]["files"], ["src/orders/features/pricing/tests/test_cap.py"])
        self.assertEqual(tasks[4]["files"], [])

    def test_plan_md_owns_line(self):
        tasks = pf.parse_plan_md(PLAN_MD)
        self.assertEqual([t["id"] for t in tasks], ["T01", "T02", "T03"])
        self.assertEqual(len(tasks[0]["files"]), 2)
        self.assertEqual(tasks[1]["files"], ["docs/trd/pricing.md"])
        self.assertEqual(tasks[2]["files"], [])

    def test_code_path(self):
        self.assertTrue(pf.is_code_path("src/orders/a.py"))
        self.assertFalse(pf.is_code_path("src/orders/features/x/CLAUDE.md"))
        self.assertFalse(pf.is_code_path("src/orders/tests/test_a.py"))
        self.assertFalse(pf.is_code_path("docs/prd/a.md"))
        self.assertFalse(pf.is_code_path("scripts/gates.sh"))


class LoadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        write(self.root, "README.md", "x\n")
        write(self.root, "changes/archive/.gitkeep", "")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "seed")
        out = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=self.root,
                             capture_output=True, text=True).stdout.split()
        self.seed = out[-1]

    def tearDown(self):
        self.tmp.cleanup()

    def test_none_when_no_plan(self):
        self.assertIsNone(pf.load_tasks(self.root, self.seed))
        self.assertEqual(pf.coverage_and_drift(None, {"src/a.py"}, ["src/a.py"]), (None, None))

    def test_reads_speckit_active_and_archived_and_legacy_plans(self):
        write(self.root, "specs/001-cap/tasks.md", TASKS_MD)
        write(self.root, "specs/001-cap/plan.md", PLAN_MD)
        write(self.root, "changes/002-x/plan.md", PLAN_MD)
        write(self.root, "changes/archive/001-y/plan.md", PLAN_MD)
        tasks = pf.load_tasks(self.root, self.seed)
        sources = sorted({t["plan"] for t in tasks})
        self.assertEqual(sources, ["changes/002-x/plan.md", "changes/archive/001-y/plan.md",
                                   "specs/001-cap/plan.md", "specs/001-cap/tasks.md"])
        self.assertEqual(len(tasks), 5 + 3 * 3)

    def test_plan_files_present_at_seed_are_ignored(self):
        write(self.root, "specs/old/tasks.md", TASKS_MD)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "more seed")
        self.assertIsNone(pf.load_tasks(self.root, self.seed + "~0") and None)
        self.assertEqual(len(pf.load_tasks(self.root, self.seed)), 5)

    def test_coverage_and_drift(self):
        tasks = pf.parse_plan_md(PLAN_MD)
        changed = {"src/orders/features/pricing/discount_calculator.py", "src/orders/other.py"}
        cov, drift = pf.coverage_and_drift(tasks, changed, sorted(changed))
        self.assertEqual(cov, 0.5)  # T01 hit, T02 not; T03 has no files and is not counted
        self.assertEqual(drift, 0.5)  # other.py is named by no task
        self.assertEqual(pf.coverage_and_drift(tasks, set(), []), (0.0, None))

    def test_directory_task_file_matches_children(self):
        tasks = [{"id": "T01", "files": ["src/orders/"]}]
        self.assertEqual(pf.coverage_and_drift(tasks, {"src/orders/a.py"}, ["src/orders/a.py"]),
                         (1.0, 0.0))


class FakeRunner:
    def __init__(self, result, code=0, cost=0.12):
        self.result, self.code, self.cost = result, code, cost
        self.calls = []

    def __call__(self, cmd, stdin, cwd):
        self.calls.append((cmd, stdin, cwd))
        return self.code, json.dumps({"result": self.result, "total_cost_usd": self.cost})


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.project, self.scn = base / "p", base / "s"
        self.project.mkdir()
        git(self.project, "init", "-q")
        write(self.project, "docs/prd/01.md", "| PRC-01 | VIP 15% | x | code |\n")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-q", "-m", "seed")
        self.seed = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=self.project,
                                   capture_output=True, text=True).stdout.split()[-1]
        write(self.project, "docs/prd/01.md",
              "| PRC-01 | VIP 15% | x | code |\n| PRC-02 | non-VIP cap 20% | x | code |\n")
        write(self.project, "changes/001/brief.md", "\n".join(f"line {i}" for i in range(100)))
        write(self.project, "docs/prd/tests_ignored.txt", "x")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-q", "-m", "work")
        write(self.scn, "decisions.md", "- cap 20%\n")
        write(self.scn, "expected.json", json.dumps({"prd_facts": [
            {"id": "f1", "fact": "regular cap 20%"}, {"id": "f2", "fact": "VIP cap 30%"},
            {"id": "f3", "fact": "rounding half up"}, {"id": "f4", "fact": "no flag"}]}))
        os.environ.pop("EVAL_NO_JUDGE", None)

    def tearDown(self):
        os.environ.pop("EVAL_NO_JUDGE", None)
        self.tmp.cleanup()

    def test_prompt_content(self):
        p = judge.build_prompt(self.project, self.scn, self.seed)
        self.assertIn("f1: regular cap 20%", p)
        self.assertIn("+| PRC-02 | non-VIP cap 20% | x | code |", p)
        self.assertIn("### changes/001/brief.md", p)
        self.assertIn("line 59", p)
        self.assertNotIn("line 60", p)
        self.assertIn("- cap 20%", p)

    def test_scores_stated_minus_contradicted(self):
        verdicts = {"facts": [{"id": "f1", "verdict": "stated"}, {"id": "f2", "verdict": "stated"},
                              {"id": "f3", "verdict": "contradicted"}, {"id": "f4", "verdict": "missing"}],
                    "restating_files": ["changes/001/brief.md"]}
        runner = FakeRunner("```json\n" + json.dumps(verdicts) + "\n```")
        r = judge.judge(self.project, self.scn, self.seed, runner=runner)
        self.assertEqual(r["prd_fidelity"], 0.25)
        self.assertEqual(r["facts"]["f3"], "contradicted")
        self.assertEqual(r["restating_files"], ["changes/001/brief.md"])
        self.assertEqual(r["judge_cost_usd"], 0.12)
        cmd, stdin, _ = runner.calls[0]
        self.assertEqual(cmd[:6], ["claude", "-p", "--model", "sonnet", "--output-format", "json"])
        self.assertEqual(cmd[-2:], ["--max-budget-usd", "0.5"])
        self.assertIn("Decisions of the change", stdin)

    def test_floor_zero_and_missing_fact_counts_as_missing(self):
        runner = FakeRunner(json.dumps({"facts": [{"id": "f1", "verdict": "contradicted"}]}))
        r = judge.judge(self.project, self.scn, self.seed, runner=runner)
        self.assertEqual(r["prd_fidelity"], 0.0)
        self.assertEqual(r["facts"]["f4"], "missing")

    def test_skip_with_env(self):
        os.environ["EVAL_NO_JUDGE"] = "1"
        runner = FakeRunner("{}")
        r = judge.judge(self.project, self.scn, self.seed, runner=runner)
        self.assertEqual(runner.calls, [])
        self.assertIsNone(r["prd_fidelity"])
        self.assertIsNone(r["judge_cost_usd"])

    def test_bad_output_returns_none_values(self):
        for runner in (FakeRunner("not json at all"), FakeRunner("{}", code=1)):
            r = judge.judge(self.project, self.scn, self.seed, runner=runner)
            self.assertIsNone(r["prd_fidelity"])
        self.assertEqual(r["judge_cost_usd"], 0.12)

    def test_runner_that_raises(self):
        def boom(cmd, stdin, cwd):
            raise OSError("no claude")
        self.assertIsNone(judge.judge(self.project, self.scn, self.seed, runner=boom)["prd_fidelity"])


if __name__ == "__main__":
    unittest.main()

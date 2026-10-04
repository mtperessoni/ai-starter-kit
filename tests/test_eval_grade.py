"""Tests of eval/grade.py on a tiny fake project."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import grade  # noqa: E402

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
    exp = {"case": case, "size": "S", "prd_facts": [{"id": "f1", "fact": "cap 20%"}],
           "dup_phrases": [r"cap of 20%"]}
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

    def test_traceability_takes_ids_from_prd_rows_added_since_seed(self):
        write(self.root, "docs/prd/01.md", PRD_SEED + "| PRC-02 | cap | src | code |\n| PRC-03 | x | src | code |\n")
        git(self.root, "commit", "-q", "-am", "prd")
        files = grade.project_files(self.root)
        self.assertEqual(grade.prd_diff_ids(self.root, self.seed), ["PRC-02", "PRC-03"])
        self.assertEqual(grade.traceability(self.root, files, self.seed), 0.5)

    def test_traceability_none_without_prd_rows(self):
        self.assertIsNone(grade.traceability(self.root, grade.project_files(self.root), self.seed))


class FakeTranscript:
    """Stands in for eval/transcript.py so grade never needs a real jsonl."""

    def __init__(self, **summary):
        self.summary = summary

    def summarize(self, path):
        return self.summary


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "proj"
        self.scenario = Path(self.tmp.name) / "scn"
        self.project.mkdir()
        make_project(self.project)
        make_scenario(self.scenario)
        self.saved = sys.modules.get("transcript")

    def tearDown(self):
        if self.saved is None:
            sys.modules.pop("transcript", None)
        else:
            sys.modules["transcript"] = self.saved
        self.tmp.cleanup()

    def status(self):
        return subprocess.run(["git", "status", "--porcelain"], cwd=self.project,
                              capture_output=True, text=True).stdout

    def commit_time(self, rev):
        out = subprocess.run(["git", "log", "-1", "--format=%ct", rev], cwd=self.project,
                             capture_output=True, text=True).stdout
        return int(out.strip())

    def test_metrics(self):
        before = self.status()
        m = grade.grade(self.project, self.scenario, "LT")
        self.assertEqual(self.status(), before)
        self.assertFalse((self.project / "tests" / "hidden").exists())
        self.assertEqual((m["hidden_passed"], m["hidden_total"], m["accept"]), (1, 2, 0.5))
        self.assertTrue(m["suite_green"])
        self.assertTrue(m["gate_ok"])
        self.assertEqual(m["traceability"], 0.0)
        self.assertTrue(m["docs_first"])
        self.assertEqual(m["planned_left"], 2)
        self.assertFalse(m["promoted"])
        self.assertEqual((m["dup_count"], m["fr_lines"], m["single_source"]), (1, 1, 2))
        self.assertEqual(m["doc_bytes"], len(PRD_NEW) - len(PRD_SEED))
        self.assertEqual(m["commits_after_seed"], 2)
        self.assertEqual((m["kit_self_fixes"], m["rework_commits"]), (0, 0))
        self.assertIsNone(m["plan_coverage"])
        self.assertIsNone(m["plan_drift"])

    def test_without_transcript_efficiency_keys_are_none(self):
        m = grade.grade(self.project, self.scenario, "LT")
        for key in ("tokens_total", "cost_usd", "wall_min", "turns", "context_peak", "subagents",
                    "tool_errors", "min_to_code", "protocol_adherence", "completed",
                    "cost_per_accept", "prd_fidelity"):
            self.assertIn(key, m)
            self.assertIsNone(m[key], key)

    def test_every_contract_metric_is_a_key(self):
        m = grade.grade(self.project, self.scenario, "LT")
        for key in ("accept", "suite_green", "gate_ok", "completed", "prd_fidelity", "plan_coverage",
                    "plan_drift", "traceability", "docs_first", "promoted", "single_source",
                    "tokens_total", "cost_usd", "wall_min", "turns", "context_peak", "subagents",
                    "min_to_code", "doc_bytes", "cost_per_accept", "tool_errors",
                    "kit_self_fixes", "rework_commits", "protocol_adherence"):
            self.assertIn(key, m)

    def test_transcript_fields_and_min_to_code(self):
        sys.modules["transcript"] = FakeTranscript(
            tokens_total=1000, cost_usd=2.0, wall_min=3.0, turns=9, context_peak=500, subagents=1,
            tool_errors=2, skills=["prd-gate", "ai-kit:other"], is_error=False)
        started = self.commit_time("HEAD") - 180
        m = grade.grade(self.project, self.scenario, "LT", transcript="t.jsonl", started_at=started)
        self.assertEqual((m["tokens_total"], m["cost_usd"], m["turns"]), (1000, 2.0, 9))
        self.assertEqual(m["cost_per_accept"], 2.0)
        self.assertAlmostEqual(m["min_to_code"], 3.0, places=1)
        self.assertEqual(m["protocol_adherence"], 1.0)
        self.assertTrue(m["completed"])

    def test_completed_false_when_run_errored(self):
        sys.modules["transcript"] = FakeTranscript(is_error=True, skills=[])
        m = grade.grade(self.project, self.scenario, "LT", transcript="t.jsonl")
        self.assertFalse(m["completed"])
        self.assertEqual(m["protocol_adherence"], 0.0)

    def test_judge_result_feeds_f1_and_f7(self):
        jr = {"prd_fidelity": 0.75, "restating_files": ["NOTES.md", "x.md"]}
        m = grade.grade(self.project, self.scenario, "LT", judge_result=jr)
        self.assertEqual(m["prd_fidelity"], 0.75)
        self.assertEqual(m["single_source"], 4)

    def test_docs_first_false_and_none(self):
        git(self.project, "reset", "-q", "--hard", "HEAD~2")
        write(self.project, "src/mod.py", "def f():\n    return 1\n# x\n")
        git(self.project, "commit", "-q", "-am", "feat: first")
        write(self.project, "docs/prd/01.md", PRD_NEW)
        git(self.project, "commit", "-q", "-am", "docs: later")
        self.assertFalse(grade.grade(self.project, self.scenario, "LT")["docs_first"])
        write(self.scenario, "expected.json", json.dumps({"case": "C3"}))
        self.assertIsNone(grade.grade(self.project, self.scenario, "LT")["docs_first"])

    def test_claude_md_under_src_is_docs_not_code(self):
        git(self.project, "reset", "-q", "--hard", "HEAD~2")
        write(self.project, "src/CLAUDE.md", "map\n")
        git(self.project, "add", "src/CLAUDE.md")
        git(self.project, "commit", "-q", "-m", "docs: map")
        write(self.project, "docs/prd/01.md", PRD_NEW)
        git(self.project, "commit", "-q", "-am", "docs: prd")
        write(self.project, "src/mod.py", "def f():\n    return 1\n# y\n")
        git(self.project, "commit", "-q", "-am", "feat: code")
        commits = grade.commit_log(self.project, grade.seed_commit(self.project))
        self.assertEqual(len(grade.code_commits(commits)), 1)
        self.assertTrue(grade.docs_first(commits))

    def test_kit_self_fixes_and_rework(self):
        write(self.project, "scripts/gates.sh", "echo\n")
        git(self.project, "add", "scripts")
        git(self.project, "commit", "-q", "-m", "fix: gates")
        write(self.project, ".specify/scripts/x.sh", "echo\n")
        git(self.project, "add", ".specify")
        git(self.project, "commit", "-q", "-m", "fix: speckit script")
        write(self.project, "src/mod.py", "def f():\n    return 3\n")
        git(self.project, "commit", "-q", "-am", "fix: again")
        write(self.project, "src/mod.py", "def f():\n    return 4\n")
        git(self.project, "commit", "-q", "-am", "chore: promote and archive")
        m = grade.grade(self.project, self.scenario, "LT")
        self.assertEqual(m["kit_self_fixes"], 2)
        self.assertEqual(m["rework_commits"], 1)

    def test_plan_coverage_and_drift(self):
        plan = ("## Constitution check\n\n### T01 · first\nOwns: src/mod.py, tests/test_mod.py\n"
                "### T02 · second\nOwns: src/never.py\n### T03 · Promote\n- PRD\n")
        write(self.project, "changes/archive/001-cap/plan.md", plan)
        write(self.project, "src/extra.py", "x = 1\n")
        git(self.project, "add", "changes", "src/extra.py")
        git(self.project, "commit", "-q", "-m", "feat: extra")
        m = grade.grade(self.project, self.scenario, "LT")
        self.assertEqual(m["plan_coverage"], 0.5)
        self.assertEqual(m["plan_drift"], 0.5)

    def test_protocol_adherence_per_arm_and_case(self):
        sk = ["prd-gate", "speckit-specify", "speckit-plan"]
        self.assertAlmostEqual(grade.protocol_adherence("SK", "C5", sk), 0.75)
        self.assertEqual(grade.protocol_adherence("SK", "C5", sk + ["speckit.tasks"]), 1.0)
        self.assertEqual(grade.protocol_adherence("LT", "C5", ["prd-gate"]), 1.0)
        self.assertEqual(grade.protocol_adherence("SK", "C3", ["prd-gate"]), 1.0)
        self.assertEqual(grade.protocol_adherence("LT", "C6", []), 0.0)
        self.assertIsNone(grade.protocol_adherence("LT", "C6", None))


if __name__ == "__main__":
    unittest.main()

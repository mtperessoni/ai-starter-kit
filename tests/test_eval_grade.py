"""Tests of eval/grade.py on a tiny fake project."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import grade  # noqa: E402
import six  # noqa: E402

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

    def test_min_to_docs_is_first_prd_commit(self):
        started = self.commit_time("HEAD~1") - 120
        m = grade.grade(self.project, self.scenario, "LT", started_at=started)
        self.assertAlmostEqual(m["min_to_docs"], 2.0, places=1)

    def test_min_to_docs_none_without_start(self):
        self.assertIsNone(grade.grade(self.project, self.scenario, "LT")["min_to_docs"])

    def test_first_pass_rate(self):
        self.assertIsNone(grade.grade(self.project, self.scenario, "LT")["first_pass_rate"])
        self.assertEqual(six.first_pass_rate(2, 4), 0.5)
        self.assertEqual(six.first_pass_rate(9, 4), 0.0)
        self.assertIsNone(six.first_pass_rate(1, 0))
        self.assertIsNone(six.first_pass_rate(None, 3))

    def test_new_transcript_fields_pass_through(self):
        sys.modules["transcript"] = FakeTranscript(
            skills=[], is_error=False, cost_main_usd=2.0, cost_subagents_usd=1.0, cache_hit_rate=0.5,
            output_share=0.1, gate_fail_ratio=0.25, rereads=3, docs_dispatched=True)
        m = grade.grade(self.project, self.scenario, "LT", transcript="t.jsonl")
        self.assertEqual((m["cost_main_usd"], m["cost_subagents_usd"], m["cache_hit_rate"]),
                         (2.0, 1.0, 0.5))
        self.assertEqual((m["output_share"], m["gate_fail_ratio"], m["rereads"]), (0.1, 0.25, 3))
        self.assertTrue(m["docs_dispatched"])

    def test_grade_carries_six_metric_fields(self):
        sys.modules["transcript"] = FakeTranscript(
            tokens_total=1000, wall_min=3.0, is_error=False, skills=[], main_min=2.0,
            agent_min=1.0, cold_starts=1, error_kinds={"other": 1}, gate_runs_main=2,
            gate_runs_sub=3)
        m = grade.grade(self.project, self.scenario, "LT", transcript="t.jsonl")
        self.assertEqual((m["main_min"], m["agent_min"], m["cold_starts"]), (2.0, 1.0, 1))
        self.assertEqual((m["gate_runs_main"], m["gate_runs_sub"]), (2, 3))
        self.assertEqual(m["error_kinds"], {"other": 1})
        self.assertIn("tasks_planned", m)
        self.assertIn("tokens_per_task", m)

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

    def test_new_keys_and_review_merge(self):
        sys.modules["transcript"] = FakeTranscript(
            tokens_total=10, wall_min=4.0, is_error=False, skills=[], tool_calls=7, error_rate=0.1,
            test_runs=2, failed_test_runs=1, review_rounds=2, tokens_main=6, tokens_subagents=4,
            subagent_detail=[{"review": False, "file_changes": 0, "started_at": None}],
            subagent_tokens_median=4, subagent_tool_calls_median=2, subagent_errors=0)
        rr = {"blind_findings": {"critical": 1, "high": 0, "medium": 0, "low": 0},
              "blind_findings_total": 1, "blind_bugs": 1, "blind_approve": False, "review_cost_usd": 0.1}
        m = grade.grade(self.project, self.scenario, "LT", transcript="t.jsonl", review_result=rr)
        self.assertEqual((m["tool_calls"], m["test_runs"], m["failed_test_runs"], m["review_rounds"]),
                         (7, 2, 1, 2))
        self.assertEqual((m["tokens_main"], m["tokens_subagents"]), (6, 4))
        self.assertEqual(m["subagents_wasted"], 1)
        self.assertEqual(m["blind_bugs"], 1)
        self.assertEqual(m["blind_critical"], 1)
        self.assertEqual(m["review_fix_commits"], 0)

    def test_new_keys_none_without_transcript(self):
        m = grade.grade(self.project, self.scenario, "LT")
        for k in ("tokens_main", "tool_calls", "review_fix_commits", "subagents_wasted",
                  "tasks_per_executor", "blind_bugs", "blind_approve"):
            self.assertIsNone(m[k], k)


class EfficiencyMetricsTest(unittest.TestCase):
    def commits(self, *times):
        return [{"time": t, "subject": f"c{t}", "files": []} for t in times]

    def test_review_fix_commits_from_reviewer_timestamp(self):
        detail = [{"review": False, "started_at": 5.0}, {"review": True, "started_at": 20.0},
                  {"review": True, "started_at": 40.0}]
        self.assertEqual(grade.review_fix_commits(self.commits(10, 25, 30), detail, True), 2)

    def test_review_fix_commits_subject_fallback_none_and_zero(self):
        cs = self.commits(1, 2, 3)
        cs[0]["subject"] = "chore: review fixes"
        self.assertEqual(grade.review_fix_commits(cs, [], True), 2)
        self.assertEqual(grade.review_fix_commits(self.commits(1, 2), [], True), 0)
        self.assertIsNone(grade.review_fix_commits(cs, [], False))

    def test_subagent_metrics(self):
        detail = [{"review": False, "file_changes": 3}, {"review": False, "file_changes": 0},
                  {"review": True, "file_changes": 0}]
        m = grade.subagent_metrics(detail, [{"id": "T1"}, {"id": "T2"}, {"id": "T3"}, {"id": "T4"}],
                                   0.5, 20.0)
        self.assertEqual(m["subagents_wasted"], 1)
        self.assertEqual(m["tasks_per_executor"], 1.0)  # 2 tasks done over 2 executors
        self.assertEqual(m["min_per_task"], 5.0)

    def test_subagent_metrics_without_plan_or_executors(self):
        m = grade.subagent_metrics([], None, None, 10.0)
        self.assertEqual((m["subagents_wasted"], m["tasks_per_executor"], m["min_per_task"]),
                         (0, None, None))

    def test_task_counts(self):
        m = grade.task_counts([{"id": "T1"}, {"id": "T2"}, {"id": "T3"}, {"id": "T4"}], 0.5, 1000)
        self.assertEqual((m["tasks_planned"], m["tasks_done"], m["tokens_per_task"]), (4, 2, 500.0))

    def test_task_counts_without_plan_or_done(self):
        m = grade.task_counts(None, None, 1000)
        self.assertEqual((m["tasks_planned"], m["tasks_done"], m["tokens_per_task"]), (0, 0, None))
        self.assertIsNone(grade.task_counts([{"id": "T1"}], 0.0, 5)["tokens_per_task"])
        self.assertIsNone(grade.task_counts([{"id": "T1"}], 1.0, None)["tokens_per_task"])

    def test_blind_metrics_merge(self):
        rr = {"blind_findings": {"critical": 0, "high": 2, "medium": 1, "low": 0},
              "blind_findings_total": 3, "blind_bugs": 1, "blind_approve": False,
              "review_cost_usd": 0.4}
        m = grade.blind_metrics(rr)
        self.assertEqual((m["blind_high"], m["blind_bugs"], m["blind_approve"]), (2, 1, False))
        self.assertIsNone(grade.blind_metrics(None)["blind_bugs"])
        self.assertIsNone(grade.blind_metrics({})["blind_high"])


def make_conflict_project(root, early_note=None, prd_edit="| PRC-03 | cap 30% | src/mod.py | code |"):
    git(root, "init", "-q")
    write(root, "docs/prd/01.md", PRD_SEED + "| PRC-03 | cap 30% | src/mod.py | code |\n")
    write(root, "src/mod.py", "def f():\n    return 1\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "chore: seed")
    if early_note:
        write(root, early_note[0], early_note[1])
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "docs: plan")
    if prd_edit:
        write(root, "docs/prd/01.md", PRD_SEED + prd_edit + "\n| PRC-09 | new cap | src/mod.py | code |\n")
        git(root, "commit", "-q", "-am", "docs: prd")


class ConflictFoundTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def found(self, texts=None, ids=("PRC-03",)):
        seed = grade.seed_commit(self.root)
        return grade.conflict_found(self.root, seed, grade.commit_log(self.root, seed), list(ids), texts)

    def test_prd_diff_editing_the_rule_counts(self):
        make_conflict_project(self.root, prd_edit="| PRC-03 | cap 20% | src/mod.py | code |")
        self.assertTrue(self.found())

    def test_untouched_rule_and_no_text_is_not_found(self):
        make_conflict_project(self.root)
        self.assertFalse(self.found([]))

    def test_assistant_text_naming_the_id_counts(self):
        make_conflict_project(self.root)
        self.assertTrue(self.found([{"t": None, "text": "This clashes with PRC-03 in pricing"}]))

    def test_assistant_text_after_the_first_prd_commit_does_not_count(self):
        make_conflict_project(self.root)
        late = grade.commit_log(self.root, grade.seed_commit(self.root))[0]["time"] + 100
        self.assertFalse(self.found([{"t": float(late), "text": "PRC-03"}]))

    def test_state_folder_note_before_the_prd_commit_counts_for_both_names(self):
        for state in (".claude/prd-flow/state/x.md", ".claude/prd-gate/state/x.md"):
            with self.subTest(state=state):
                tmp = tempfile.TemporaryDirectory()
                root = Path(tmp.name)
                make_conflict_project(root, early_note=(state, "conflict with PRC-03\n"))
                seed = grade.seed_commit(root)
                self.assertTrue(grade.conflict_found(root, seed, grade.commit_log(root, seed), ["PRC-03"], []))
                tmp.cleanup()

    def test_untracked_state_note_older_than_the_prd_commit_counts(self):
        make_conflict_project(self.root)
        note = write(self.root, ".claude/prd-flow/state/s/impact.md", "clashes with PRC-03\n")
        cut = grade.commit_log(self.root, grade.seed_commit(self.root))[0]["time"]
        os.utime(note, (cut - 60, cut - 60))
        self.assertTrue(self.found([]))
        os.utime(note, (cut + 60, cut + 60))
        self.assertFalse(self.found([]))

    def test_changes_note_after_the_prd_commit_does_not_count(self):
        make_conflict_project(self.root)
        write(self.root, "changes/001-x/brief.md", "mentions PRC-03\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "docs: brief")
        self.assertFalse(self.found([]))

    def test_no_ids_expected_is_none(self):
        make_conflict_project(self.root)
        seed = grade.seed_commit(self.root)
        self.assertIsNone(grade.conflict_found(self.root, seed, [], [], []))


class SkillNameTest(unittest.TestCase):
    def test_protocol_adherence_accepts_either_skill_name(self):
        for name in ("prd-flow", "prd-gate", "ai-kit:prd-flow", "/prd-gate"):
            self.assertEqual(grade.protocol_adherence("LT", "C5", [name]), 1.0, name)
        self.assertEqual(grade.protocol_adherence("LT", "C5", ["prd-create"]), 0.0)

    def test_speckit_arm_with_flow_skill(self):
        sk = ["prd-flow", "speckit-specify", "speckit-plan", "speckit-tasks"]
        self.assertEqual(grade.protocol_adherence("SK", "C5", sk), 1.0)

    def test_gate_ok_resolves_the_flow_path(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(grade.gate_ok(d))
            write(d, ".claude/skills/prd-flow/scripts/gate.py", "import sys\nsys.exit(0)\n")
            self.assertTrue(grade.gate_ok(d))

    def test_state_folders_are_not_counted_as_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            git(d, "init", "-q")
            write(d, "README.md", "x\n")
            git(d, "add", "-A")
            git(d, "commit", "-q", "-m", "seed")
            write(d, ".claude/prd-flow/state/n.md", "cap of 20%\n")
            self.assertEqual(grade.dup_count(d, grade.project_files(d), [r"cap of 20%"], None), 0)


class JudgeKeysTest(unittest.TestCase):
    def test_judge_result_feeds_the_k91_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, scenario = Path(tmp) / "p", Path(tmp) / "s"
            project.mkdir()
            make_project(project)
            make_scenario(scenario)
            jr = {"contradiction_left": 1, "gap_recorded": True}
            m = grade.grade(project, scenario, "LT", judge_result=jr)
            self.assertEqual((m["contradiction_left"], m["gap_recorded"]), (1, True))
            self.assertIsNone(m["conflict_found"])
            write(scenario, "expected.json", json.dumps({"case": "C5", "conflict_ids": ["PRC-01"]}))
            self.assertIn(grade.grade(project, scenario, "LT")["conflict_found"], (True, False))


if __name__ == "__main__":
    unittest.main()

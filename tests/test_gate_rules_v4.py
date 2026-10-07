"""gate.py Q3 (interview), Q4 (--applied), G30 (proposed at --final), --status and G27 (remote branches)."""

import tempfile
import unittest
from pathlib import Path

from tests.test_kit_scripts import Project, run, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
RULES = "state/orders/approved-rules.md"
INTERVIEW = "state/orders/interview.md"
NEW_ROW = "| ORD-03 | Orders can be reopened. | planned | code |"
ORD1 = "| ORD-01 | An order is created only from a cart with at least one item. | src/features/orders/order_service.py::create_order | code |"
DIMENSIONS = [f"D{n:02d}" for n in range(1, 16)]
CONFIRMED = 'Confirmed: Ana · 2026-10-07 · "go"'
FOLLOW_UP = "\n## Dimensions (2026-10-08)\n| Dimension | State | Answer |\n|---|---|---|\n| D05 failures | user | y |\n"


def approved(row: str) -> str:
    return f"# Approved\n\n## shop/05-orders.md\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n{row}\n"


def interview(dims: list[str] | None = None, state: str = "doc", answer: str = "x", confirmed: bool = True) -> str:
    rows = "\n".join(f"| {d} thing | {state} | {answer} |" for d in (DIMENSIONS if dims is None else dims))
    tail = f"\n{CONFIRMED}\n" if confirmed else "\n"
    return f"# Interview\n\n## Dimensions\n| Dimension | State | Answer |\n|---|---|---|\n{rows}\n{tail}"


class InterviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        write(self.p.root, RULES, approved(NEW_ROW))

    def tearDown(self) -> None:
        self.p.close()

    def gate(self):
        return self.p.py(GATE, "--rules", RULES)

    def put(self, text: str) -> None:
        write(self.p.root, INTERVIEW, text)

    def test_a_missing_interview_is_q3(self) -> None:
        r = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR Q3", r.stdout)

    def test_a_complete_confirmed_interview_passes(self) -> None:
        self.put(interview())
        r = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("Q3", r.stdout)

    def test_a_missing_dimension_is_q3(self) -> None:
        self.put(interview([d for d in DIMENSIONS if d != "D07"]))
        r = self.gate()
        self.assertIn("ERROR Q3", r.stdout)
        self.assertIn("D07", r.stdout)

    def test_a_state_outside_the_set_is_q3(self) -> None:
        self.put(interview(state="open"))
        self.assertIn("ERROR Q3", self.gate().stdout)

    def test_a_question_needs_an_existing_q_id(self) -> None:
        self.put(interview(state="question", answer="Q-99"))
        self.assertIn("ERROR Q3", self.gate().stdout)
        write(self.p.root, RULES, approved(NEW_ROW) + "\nQ-99 pending decision\n")
        self.assertNotIn("ERROR Q3", self.gate().stdout)

    def test_a_question_without_a_q_id_is_q3(self) -> None:
        self.put(interview(state="question", answer="later"))
        self.assertIn("ERROR Q3", self.gate().stdout)

    def test_a_table_without_confirmed_is_q3(self) -> None:
        self.put(interview(confirmed=False))
        self.assertIn("ERROR Q3", self.gate().stdout)

    def test_a_follow_up_table_needs_a_confirmed_line(self) -> None:
        self.put(interview() + FOLLOW_UP)
        self.assertIn("ERROR Q3", self.gate().stdout)
        self.put(interview() + FOLLOW_UP + f"\n{CONFIRMED}\n")
        self.assertNotIn("ERROR Q3", self.gate().stdout)

    def test_a_follow_up_table_needs_a_reopened_dimension(self) -> None:
        self.put(interview() + f"\n## Dimensions (2026-10-08)\n| Dimension | State | Answer |\n|---|---|---|\n\n{CONFIRMED}\n")
        self.assertIn("ERROR Q3", self.gate().stdout)

    def test_a_confirmed_line_in_a_later_section_does_not_count(self) -> None:
        self.put(interview(confirmed=False) + f"\n## Notes\n{CONFIRMED}\n")
        self.assertIn("ERROR Q3", self.gate().stdout)

    def test_a_short_c5_outside_a_c5_needs_only_its_listed_dimensions(self) -> None:
        scope = "Scope: short C5 outside a C5\n\n"
        text = scope + interview(["D05"], confirmed=True).replace("## Dimensions", "## Dimensions (2026-10-08)")
        self.put(text)
        self.assertNotIn("ERROR Q3", self.gate().stdout)
        self.put(scope + interview([], confirmed=True).replace("## Dimensions", "## Dimensions (2026-10-08)"))
        self.assertIn("ERROR Q3", self.gate().stdout)

    def test_a_dated_first_block_without_the_scope_line_needs_every_dimension(self) -> None:
        self.put(interview(["D05"], confirmed=True).replace("## Dimensions", "## Dimensions (2026-10-08)"))
        out = self.gate().stdout
        self.assertIn("ERROR Q3", out)
        self.assertIn("D01", out)

    def test_an_extra_dimension_is_required_and_a_placeholder_is_not(self) -> None:
        self.put(interview())
        self.assertNotIn("D16", self.gate().stdout)
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        text = repo.read_text(encoding="utf-8")
        self.assertIn("| D16 | `<", text)
        repo.write_text(text.replace("| D16 | `<", "| D16 | Pricing | cost? |\n| D17 | `<", 1), encoding="utf-8")
        out = self.gate().stdout
        self.assertIn("D16", out)
        self.assertNotIn("D17", out)


class AppliedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        write(self.p.root, INTERVIEW, interview())

    def tearDown(self) -> None:
        self.p.close()

    def gate(self, row: str):
        write(self.p.root, RULES, approved(row))
        return self.p.py(GATE, "--rules", RULES, "--applied")

    def test_an_identical_row_passes_even_with_other_spacing(self) -> None:
        r = self.gate(ORD1.replace("only from", "only   from"))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_different_row_is_q4(self) -> None:
        self.assertIn("ERROR Q4", self.gate(ORD1.replace("at least one", "two")).stdout)

    def test_a_row_not_in_the_prd_is_q4(self) -> None:
        self.assertIn("ERROR Q4", self.gate(NEW_ROW).stdout)

    def test_a_file_name_that_only_ends_the_same_is_not_the_same_file(self) -> None:
        write(self.p.root, RULES, approved(ORD1).replace("## shop/05-orders.md", "## 5-orders.md"))
        self.assertIn("ERROR Q4", self.p.py(GATE, "--rules", RULES, "--applied").stdout)
        self.assertIn("ERROR Q2", self.p.py(GATE, "--rules", RULES).stdout)

    def test_a_later_dated_section_replaces_an_earlier_row(self) -> None:
        later = ORD1.replace("at least one item", "two items")
        text = approved(ORD1) + f"\n## 2026-10-08\n\n### shop/05-orders.md\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n{later}\n"
        write(self.p.root, RULES, text)
        r = self.p.py(GATE, "--rules", RULES, "--applied")
        self.assertNotIn("repeated", r.stdout)
        self.assertIn("ERROR Q4", r.stdout)
        self.assertEqual(r.stdout.count("ERROR Q4"), 1, r.stdout)
        write(self.p.root, RULES, text.replace(later, ORD1))
        r = self.p.py(GATE, "--rules", RULES, "--applied")
        self.assertNotIn("Q4", r.stdout)
        self.assertNotIn("repeated", r.stdout)

    def test_a_row_under_a_date_before_any_file_heading_binds_to_no_file(self) -> None:
        stray = ORD1.replace("at least one item", "two items")
        text = approved(ORD1) + f"\n## 2026-10-08\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n{stray}\n"
        write(self.p.root, RULES, text)
        r = self.p.py(GATE, "--rules", RULES, "--applied")
        self.assertNotIn("ERROR Q4", r.stdout)

    def test_without_the_flag_q4_does_not_run(self) -> None:
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("Q4", self.p.py(GATE, "--rules", RULES).stdout)


class ChangeViaColumnTest(unittest.TestCase):
    def test_a_table_with_an_example_column_is_a_rule_table(self) -> None:
        p = Project()
        try:
            path = p.root / ORDERS
            path.write_text(path.read_text(encoding="utf-8") + "\n| ID | Rule | Source | Change via | Example |\n|---|---|---|---|---|\n"
                            "| ORD-03 | Orders can be reopened. | src/x.py | bogus | a cart |\n", encoding="utf-8", newline="\n")
            self.assertIn("WARNING G3", p.py(GATE, "--base", "HEAD").stdout)
        finally:
            p.close()


class ProposedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        path = self.p.root / ORDERS
        text = path.read_text(encoding="utf-8")
        old = "(`OrderConfig.timeout`). | src/features/orders/order_service.py"
        path.write_text(text.replace(old, "(`OrderConfig.timeout`). *(proposed)* | planned"), encoding="utf-8", newline="\n")

    def tearDown(self) -> None:
        self.p.close()

    def test_final_fails_g30_and_not_g19_for_a_proposed_row(self) -> None:
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G30", r.stdout)
        self.assertNotIn("G19", r.stdout)

    def test_a_proposed_row_with_another_source_warns_g9(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("*(proposed)* | planned", "*(proposed)* | src/x.py"), encoding="utf-8", newline="\n")
        self.assertIn("WARNING G9", self.p.py(GATE).stdout)

    def test_status_reports_proposed_and_implemented(self) -> None:
        out = self.p.py(GATE, "--status").stdout
        self.assertIn("ORD-01 · implemented · shop/05-orders.md · src/features/orders/order_service.py::create_order · code", out)
        self.assertIn("ORD-02 · proposed · shop/05-orders.md · planned · config", out)

    def test_status_filters(self) -> None:
        out = self.p.py(GATE, "--status", "--state", "proposed").stdout
        self.assertIn("ORD-02", out)
        self.assertNotIn("ORD-01", out)
        self.assertNotIn("ORD-02", self.p.py(GATE, "--status", "--prd", "other").stdout)
        self.assertIn("ORD-02", self.p.py(GATE, "--status", "--prd", "docs/prd/shop").stdout)

    def test_status_marks_pending_code_as_approved(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("*(proposed)*", "*(approved 2026-10-07, pending code)*"), encoding="utf-8", newline="\n")
        self.assertIn("ORD-02 · approved", self.p.py(GATE, "--status").stdout)


class RemoteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.bare = tempfile.TemporaryDirectory()
        run(Path(self.bare.name), "git", "init", "-q", "--bare", "-b", "main", check=True)
        run(self.p.root, "git", "remote", "add", "origin", self.bare.name, check=True)
        run(self.p.root, "git", "push", "-q", "origin", "main", check=True)

    def tearDown(self) -> None:
        self.p.close()
        self.bare.cleanup()

    def push_branch(self, rel: str, text: str) -> None:
        run(self.p.root, "git", "checkout", "-q", "-b", "feat", check=True)
        write(self.p.root, rel, text)
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "feat", check=True)
        run(self.p.root, "git", "push", "-q", "origin", "feat", check=True)
        run(self.p.root, "git", "checkout", "-q", "main", check=True)
        write(self.p.root, INTERVIEW, interview())

    def test_a_new_id_used_on_a_remote_branch_warns_g27(self) -> None:
        self.push_branch(ORDERS, (self.p.root / ORDERS).read_text(encoding="utf-8") + NEW_ROW + "\n")
        write(self.p.root, RULES, approved(NEW_ROW))
        r = self.p.py(GATE, "--rules", RULES)
        self.assertIn("WARNING G27", r.stdout)
        self.assertIn("ORD-03", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_id_unused_on_remotes_is_silent(self) -> None:
        self.push_branch("docs/other.md", "x\n")
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("G27", self.p.py(GATE, "--rules", RULES).stdout)

    def test_a_change_number_used_on_a_remote_branch_warns_g27(self) -> None:
        self.push_branch("changes/001-other/brief.md", "# Brief\n\nSize: S\n")
        write(self.p.root, "changes/001-limit/brief.md", "# Brief\n\nSize: S\n")
        r = self.p.py(GATE, "--change", "changes/001-limit")
        self.assertIn("WARNING G27", r.stdout)
        self.assertIn("001-other", r.stdout)

    def test_the_same_change_folder_on_a_remote_is_not_a_clash(self) -> None:
        self.push_branch("changes/001-limit/brief.md", "# Brief\n\nSize: S\n")
        write(self.p.root, "changes/001-limit/brief.md", "# Brief\n\nSize: S\n")
        self.assertNotIn("G27", self.p.py(GATE, "--change", "changes/001-limit").stdout)

    def test_the_upstream_of_the_current_branch_is_skipped(self) -> None:
        run(self.p.root, "git", "checkout", "-q", "-b", "feat", check=True)
        write(self.p.root, ORDERS, (self.p.root / ORDERS).read_text(encoding="utf-8") + NEW_ROW + "\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "feat", check=True)
        run(self.p.root, "git", "push", "-q", "-u", "origin", "feat", check=True)
        write(self.p.root, INTERVIEW, interview())
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("G27", self.p.py(GATE, "--rules", RULES).stdout)

    def test_no_remote_is_silent(self) -> None:
        run(self.p.root, "git", "remote", "remove", "origin", check=True)
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("G27", self.p.py(GATE, "--rules", RULES).stdout)


class ConfigDefaultsTest(unittest.TestCase):
    def test_older_adapters_keep_working(self) -> None:
        p = Project()
        try:
            repo = p.root / ".claude/skills/prd-flow/repo.md"
            drop = ("| proposed_marker", "| html_mode", "| html_template", "| trd_budget_lines")
            lines = [ln for ln in repo.read_text(encoding="utf-8").splitlines() if not ln.startswith(drop)]
            repo.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual(p.py(GATE).returncode, 0)
        finally:
            p.close()


if __name__ == "__main__":
    unittest.main()

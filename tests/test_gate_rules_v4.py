"""gate.py Q2 (rules skeleton), Q4 (--applied), G30 (proposed at --final), --status and G27 (remote branches)."""

import tempfile
import unittest
from pathlib import Path

from tests.test_kit_scripts import Project, run, write
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
RULES = "state/orders/approved-rules.md"
NEW_ROW = "| ORD-03 | Orders can be reopened. | planned | code |"
ORD1 = "| ORD-01 | An order is created only from a cart with at least one item. | src/features/orders/order_service.py::create_order | code |"


def approved(row: str) -> str:
    return f"# Approved\n\n## shop/05-orders.md\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n{row}\n"


class RulesSkeletonTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def out(self, text: str) -> str:
        write(self.p.root, RULES, text)
        return self.p.py(GATE, "--rules", RULES).stdout

    def assertSkeleton(self, out: str) -> None:
        self.assertIn("ERROR Q2", out)
        self.assertEqual(out.count("HINT ## <prd file>.md"), 1, out)
        self.assertIn("HINT | ID | Rule | Source | Change via | Example |", out)
        self.assertIn("(approved YYYY-MM-DD, pending code)", out)
        self.assertIn("| planned | code |", out)
        self.assertIn("## Supersedes", out)

    def test_free_form_rules_print_the_skeleton(self) -> None:
        self.assertSkeleton(self.out("# Approved\n\n- ORD-03 orders can be reopened\n"))

    def test_a_row_with_a_wrong_column_count_prints_the_skeleton(self) -> None:
        self.assertSkeleton(self.out(approved("| ORD-03 | Orders can be reopened. |")))

    def test_a_wrong_change_via_prints_the_skeleton(self) -> None:
        self.assertSkeleton(self.out(approved("| ORD-03 | Orders can be reopened. | planned | magic |")))

    def test_a_valid_rules_file_prints_no_hint(self) -> None:
        self.assertNotIn("HINT", self.out(approved(NEW_ROW)))


class AppliedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

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
            self.assertIn("WARNING G3", full(p, p.py(GATE, "--base", "HEAD")))
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
        self.assertIn("WARNING G9", full(self.p, self.p.py(GATE)))

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

    def test_a_new_id_used_on_a_remote_branch_warns_g27(self) -> None:
        self.push_branch(ORDERS, (self.p.root / ORDERS).read_text(encoding="utf-8") + NEW_ROW + "\n")
        write(self.p.root, RULES, approved(NEW_ROW))
        r = self.p.py(GATE, "--rules", RULES)
        self.assertIn("WARNING G27", full(self.p, r))
        self.assertIn("ORD-03", full(self.p, r))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_id_unused_on_remotes_is_silent(self) -> None:
        self.push_branch("docs/other.md", "x\n")
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("G27", self.p.py(GATE, "--rules", RULES).stdout)

    def test_a_change_number_used_on_a_remote_branch_warns_g27(self) -> None:
        self.push_branch("changes/001-other/brief.md", "# Brief\n\nSize: S\n")
        write(self.p.root, "changes/001-limit/brief.md", "# Brief\n\nSize: S\n")
        r = self.p.py(GATE, "--change", "changes/001-limit")
        self.assertIn("WARNING G27", full(self.p, r))
        self.assertIn("001-other", full(self.p, r))

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
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("G27", self.p.py(GATE, "--rules", RULES).stdout)

    def test_no_remote_is_silent(self) -> None:
        run(self.p.root, "git", "remote", "remove", "origin", check=True)
        write(self.p.root, RULES, approved(NEW_ROW))
        self.assertNotIn("G27", self.p.py(GATE, "--rules", RULES).stdout)


PENDING = "| ORD-03 | *(approved 2026-10-07, pending code)* Orders can be reopened. | planned | code |"
LOG = "docs/prd/CHANGELOG.md"
ENTRY = """# CHANGELOG

## Reopen orders (2026-10-07, Ana, changes/001-orders)

Reason: orders can be reopened. IDs: ORD-03.
Conflicts: ORD-01 compatible (reopening keeps the cart rule).
Supersedes: none.

### shop/05-orders.md

**ORD-03** (whole row), new.
"""
DECISIONS = """# Decisions · 001-orders

Reply 1: "reopen within 7 days, ok"

| ID | Question | Decision | Rejected alternative | Why | Rules |
|---|---|---|---|---|---|
| DEC-01 | Window? | 7 days | none | simple | ORD-03 |
"""


class NewRouteTest(unittest.TestCase):
    """No approved-rules.md or rules.md: the approved set is the CHANGELOG entry of the slug."""

    def setUp(self) -> None:
        self.p = Project()
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + PENDING + "\n", encoding="utf-8", newline="\n")
        write(self.p.root, LOG, ENTRY)
        write(self.p.root, "changes/001-orders/decisions.md", DECISIONS)
        write(self.p.root, "state/orders/sheet.md", "# Sheet\n")

    def tearDown(self) -> None:
        self.p.close()

    def gate(self, *extra: str) -> str:
        return full(self.p, self.p.py(GATE, "--rules", RULES, *extra))

    def test_a_valid_entry_passes_without_answers_md(self) -> None:
        self.assertFalse((self.p.root / "state/orders/answers.md").exists())
        out = self.gate("--applied")
        self.assertNotIn("ERROR", out)
        self.assertNotIn("Traceback", out)

    def test_no_entry_is_q2(self) -> None:
        write(self.p.root, LOG, "# CHANGELOG\n")
        self.assertIn("ERROR Q2 no CHANGELOG entry", self.gate())

    def test_an_id_missing_from_the_prd_is_q2(self) -> None:
        write(self.p.root, LOG, ENTRY.replace("IDs: ORD-03.", "IDs: ORD-03, ORD-09."))
        self.assertIn("ERROR Q2 ORD-09 is in the IDs of the CHANGELOG entry and not in the PRD", self.gate())

    def test_an_id_without_the_pending_marker_is_q2_before_promote(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("*(approved 2026-10-07, pending code)* ", ""), encoding="utf-8", newline="\n")
        self.assertIn("ERROR Q2 ORD-03 is in the IDs of the CHANGELOG entry and its PRD row has no pending marker", self.gate())

    def test_after_promote_the_marker_must_be_gone(self) -> None:
        write(self.p.root, LOG, ENTRY + "\nPromoted: sources set.\n")
        self.assertIn("ERROR Q4 ORD-03 still carries the pending marker after promote", self.gate())
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("*(approved 2026-10-07, pending code)* ", ""), encoding="utf-8", newline="\n")
        self.assertNotIn("ERROR", self.gate())

    def test_a_pack_conflict_must_be_in_the_entry(self) -> None:
        write(self.p.root, "state/orders/pack.md", "# Pack\nConflicts: ORD-01, ORD-02\n")
        out = self.gate()
        self.assertNotIn("ORD-01 is in the Conflicts", out)
        self.assertIn("ERROR Q5 ORD-02 is in the Conflicts of pack.md and not in the IDs, Supersedes or Conflicts", out)

    def test_a_mechanism_term_must_come_from_the_sheet_or_a_reply(self) -> None:
        write(self.p.root, "changes/001-orders/decisions.md", DECISIONS.replace("| 7 days |", "| 7 days via an environment variable |"))
        self.assertIn("ERROR Q3 the mechanism 'environment variable'", self.gate())
        write(self.p.root, "state/orders/sheet.md", "# Sheet\nuse an environment variable\n")
        self.assertNotIn("ERROR Q3", self.gate())
        write(self.p.root, "state/orders/sheet.md", "# Sheet\n")
        write(self.p.root, "changes/001-orders/decisions.md",
              DECISIONS.replace("ok", "ok, an environment variable").replace("| 7 days |", "| 7 days via an environment variable |"))
        self.assertNotIn("ERROR Q3", self.gate())

    def test_a_reply_line_is_not_itself_scanned_for_mechanisms(self) -> None:
        write(self.p.root, "changes/001-orders/decisions.md", DECISIONS.replace("ok", "ok, a new table"))
        self.assertNotIn("ERROR Q3", self.gate())

    def test_a_mechanism_term_in_a_row_of_the_ids_is_scanned(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("Orders can be reopened.", "Orders can be reopened through a new endpoint."), encoding="utf-8", newline="\n")
        self.assertIn("ERROR Q3 the mechanism 'endpoint'", self.gate())

    def test_the_old_route_wins_while_the_state_folder_has_approved_rules(self) -> None:
        write(self.p.root, RULES, approved(PENDING))
        self.assertNotIn("CHANGELOG", self.gate())


class WarningsLineTest(unittest.TestCase):
    def test_stdout_is_the_errors_and_one_warnings_line(self) -> None:
        p = Project()
        try:
            path = p.root / ORDERS
            path.write_text(path.read_text(encoding="utf-8") + "\n| ID | Rule | Source | Change via | Example |\n|---|---|---|---|---|\n"
                            "| ORD-03 | Orders can be reopened. | src/x.py | bogus | a cart |\n", encoding="utf-8", newline="\n")
            r = p.py(GATE, "--base", "HEAD")
            self.assertNotIn("WARNING", r.stdout)
            self.assertRegex(r.stdout.strip().splitlines()[-1], r"^warnings: [1-9]\d* \(see \.claude/prd-flow/state/_gate/last-default\.txt\)$")
            self.assertIn("WARNING G3", full(p, r))
        finally:
            p.close()


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

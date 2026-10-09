"""promote.py: the mechanical part of the Promote task, on a throwaway project with a real git repository."""

import re
import shutil
import unittest

from tests.test_kit_scripts import KIT, Project, run, write

PROMOTE = ".claude/skills/prd-flow/scripts/promote.py"
PRD = "docs/prd/shop/05-orders.md"
STATE = ".claude/prd-flow/state/disc"

PRD_TEXT = """\
## 05. Step 1 · Orders

An order is created from a cart.

| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-01 | An order is created only from a cart with at least one item. | src/features/orders/order_service.py::create_order | code |
| ORD-02 | *(approved 2026-10-04, pending code)* An unpaid order is cancelled after 20 s. | planned | config |
| ORD-03 | *(approved 2026-10-04, pending code)* A paid order is shipped. | planned | code |
| ORD-04 | *(approved 2026-10-04, pending code)* A refund keeps the invoice. | planned | code |
"""

APPROVED = """\
# Approved rules · disc · 2026-10-04 · Ana
## docs/prd/shop/05-orders.md
| ORD-02 | *(approved 2026-10-04, pending code)* An unpaid order is cancelled after 20 s. | planned | config |
| ORD-03 | *(approved 2026-10-04, pending code)* A paid order is shipped. | planned | code |
| ORD-04 | *(approved 2026-10-04, pending code)* A refund keeps the invoice. | planned | code |
## Supersedes
- ORD-02 (An unpaid order is cancelled after 30 s.)
- ORD-01 (An order is created only from a cart with at least one item.)
"""

DECISIONS = """\
# Decisions · 001-disc

| ID | Question | Decision | Rejected alternative | Why | Rules |
|---|---|---|---|---|---|
| DEC-01 | How long to wait? | 20 s | 30 s | carts expire | ORD-02 |
"""

DELIVERIES = """\
## T01
Source: ORD-02 src/features/orders/order_service.py::cancel_unpaid
Source: ORD-03 src/features/orders/ship.py
"""

TRD = """\
# orders

## Planned (disc, feat/disc)

| File | Changes or creates | Symbols | IDs |
|---|---|---|---|
| `src/features/orders/refund.py` | creates | `refund` | ORD-04 |
"""


class PromoteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        r = self.p.root
        shutil.copytree(KIT / "docs" / "templates", r / "docs" / "templates", dirs_exist_ok=True)
        write(r, PRD, PRD_TEXT)
        write(r, f"{STATE}/approved-rules.md", APPROVED)
        write(r, f"{STATE}/deliveries.md", DELIVERIES)
        write(r, f"{STATE}/state.md", "state\n")
        write(r, "docs/trd/orders.md", TRD)
        write(r, "changes/001-disc/decisions.md", DECISIONS)
        write(r, "changes/001-disc/plan.md", "plan\n")
        run(r, "git", "add", "-A", check=True)
        run(r, "git", "commit", "-q", "-m", "approved", check=True)

    def tearDown(self) -> None:
        self.p.close()

    def promote(self, *extra: str):
        return self.p.py(PROMOTE, "disc", *extra)

    def text(self, rel: str) -> str:
        return (self.p.root / rel).read_text(encoding="utf-8")

    def test_open_question_and_decision_rows_are_not_rules(self) -> None:
        extra = "| Q-ORD-01 | Should refunds be partial? | planned | code |\n| DEC-02 | x | planned | code |\n"
        write(self.p.root, f"{STATE}/approved-rules.md", APPROVED.replace("## Supersedes", extra + "## Supersedes"))
        write(self.p.root, PRD, PRD_TEXT + "| Q-ORD-01 | *(approved 2026-10-04, pending code)* Partial refunds? | planned | code |\n")
        r = self.promote("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Q-ORD-01", r.stdout)
        self.assertIn("3 approved", r.stdout)

    def test_dry_run_changes_nothing_and_prints_at_most_ten_lines(self) -> None:
        def status() -> list[str]:
            return [ln for ln in run(self.p.root, "git", "status", "--porcelain").stdout.splitlines() if "__pycache__" not in ln]

        before = status()
        r = self.promote("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 14)
        self.assertIn("dry-run", r.stdout)
        self.assertEqual(status(), before)
        self.assertTrue((self.p.root / "changes/001-disc").is_dir())

    def test_markers_leave_and_sources_come_from_deliveries_then_the_trd(self) -> None:
        r = self.promote()
        out = r.stdout + r.stderr
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 14, out)
        prd = self.text(PRD)
        self.assertNotIn("pending code", prd)
        self.assertIn("| ORD-02 | An unpaid order is cancelled after 20 s. | src/features/orders/order_service.py::cancel_unpaid | config |", prd)
        self.assertIn("| src/features/orders/ship.py | code |", prd)
        self.assertIn("| src/features/orders/refund.py | code |", prd)

    def test_sources_come_from_the_per_task_delivery_files(self) -> None:
        (self.p.root / STATE / "deliveries.md").unlink()
        write(self.p.root, f"{STATE}/deliveries/T01.md", "Source: ORD-02 src/a.py::cancel" + chr(10))
        write(self.p.root, f"{STATE}/deliveries/T02.md", "Source: ORD-03 src/b.py" + chr(10))
        self.promote()
        prd = self.text(PRD)
        self.assertIn("| ORD-02 | An unpaid order is cancelled after 20 s. | src/a.py::cancel | config |", prd)
        self.assertIn("| src/b.py | code |", prd)

    def test_success_prints_the_files_changed_and_a_ready_commit_message(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("files:", r.stdout)
        self.assertIn(PRD, r.stdout)
        self.assertIn("docs/prd/CHANGELOG.md", r.stdout)
        self.assertIn("commit: docs(prd): promote disc", r.stdout)
        self.assertRegex(r.stdout, r"Rules: .*ORD-02")

    def test_a_missing_source_names_the_executor_fix_as_owner(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("", encoding="utf-8")
        r = self.promote()
        self.assertIn("owner: executor fix", r.stdout)
        self.assertIn("next: executor fix", r.stdout)

    def test_a_missing_approved_rules_file_names_the_user_as_owner(self) -> None:
        (self.p.root / STATE / "approved-rules.md").unlink()
        r = self.promote()
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("owner: user", r.stdout)
        self.assertNotIn("owner: executor fix", r.stdout)
        self.assertNotIn("owner: surveyor", r.stdout)
        self.assertIn("next: ", r.stdout)

    def test_a_missing_prd_file_prints_an_owner_and_next(self) -> None:
        shutil.rmtree(self.p.root / "docs/prd/shop")
        r = self.promote()
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("owner: ", r.stdout)
        self.assertIn("next: ", r.stdout)

    def test_a_warning_on_success_names_its_dispatch(self) -> None:
        write(self.p.root, "docs/prd/shop/09-orders-amendment.md", "# amendment" + chr(10))
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN amendment file", r.stdout)
        self.assertIn("next: docs fold", r.stdout)
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 14, r.stdout)

    def test_a_superseded_mismatch_names_docs_fold_as_owner(self) -> None:
        path = self.p.root / STATE / "approved-rules.md"
        path.write_text(APPROVED + "- ORD-77: Ghost." + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertIn("owner: docs fold", r.stdout)
        self.assertIn("next: docs fold", r.stdout)

    def test_a_superseded_row_leaves_the_prd(self) -> None:
        self.promote()
        self.assertNotIn("| ORD-01 |", self.text(PRD))

    def test_the_changelog_keeps_old_text_literally_and_the_decisions(self) -> None:
        self.promote()
        log = self.text("docs/prd/CHANGELOG.md")
        self.assertIn("An unpaid order is cancelled after 30 s.", log)
        self.assertIn("An order is created only from a cart with at least one item.", log)
        self.assertIn("| DEC-01 | How long to wait? | 20 s | 30 s | carts expire | ORD-02 |", log)
        self.assertIn("Ana", log)
        self.assertLess(log.index("## "), log.index("DEC-01"))

    def test_the_change_folder_is_archived_and_the_state_is_kept_for_close(self) -> None:
        self.promote()
        self.assertTrue((self.p.root / "changes/archive/001-disc/plan.md").is_file())
        self.assertFalse((self.p.root / "changes/001-disc").exists())
        left = sorted(x.name for x in (self.p.root / STATE).iterdir())
        self.assertEqual(left, ["approved-rules.md", "deliveries.md", "state.md"])

    def test_a_rerun_skips_what_is_done_and_adds_no_second_changelog_entry(self) -> None:
        self.promote()
        r = self.promote()
        self.assertIn("already archived", r.stdout)
        self.assertEqual(self.text("docs/prd/CHANGELOG.md").count("## disc ("), 1)

    def test_superseded_ids_are_dropped_from_every_file_not_only_the_first(self) -> None:
        write(self.p.root, "docs/prd/shop/06-other.md", "| ID | Rule | Source | Change via |\n|---|---|---|---|\n| ORD-09 | Old rule. | src/x.py | code |\n")
        path = self.p.root / STATE / "approved-rules.md"
        path.write_text(APPROVED + "- ORD-09: Old rule.\n", encoding="utf-8")
        self.promote()
        self.assertNotIn("| ORD-09 |", self.text("docs/prd/shop/06-other.md"))
        self.assertIn("Old rule.", self.text("docs/prd/CHANGELOG.md"))

    def test_a_superseded_id_matching_no_row_is_an_error_naming_it(self) -> None:
        path = self.p.root / STATE / "approved-rules.md"
        path.write_text(APPROVED + "- ORD-77: Ghost.\n", encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ORD-77", r.stdout)
        self.assertTrue((self.p.root / "changes/001-disc").is_dir())

    def test_promote_has_no_html_step_and_never_mentions_html(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("html", r.stdout.lower())
        self.assertNotIn("ORD-03", self.text("docs/prd/prd.html"))

    def test_the_final_gate_is_scoped_to_the_slug_so_another_changes_planned_section_only_warns(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        write(self.p.root, "docs/trd/billing.md", "# Billing" + chr(10) + chr(10) + "## Planned (002-other)" + chr(10) + "BIL-01 moves." + chr(10))
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_runs_the_final_gate_and_prints_its_last_line(self) -> None:
        r = self.promote()
        self.assertIn("gate --final:", r.stdout)

    def test_a_row_without_a_source_keeps_its_marker_and_fails_listing_the_id(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("", encoding="utf-8")
        before = self.text(PRD)
        r = self.promote()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ORD-04", r.stdout)
        self.assertIn("Source", r.stdout)
        self.assertEqual(self.text(PRD), before)
        self.assertTrue((self.p.root / STATE / "approved-rules.md").is_file())

    def test_a_non_code_rule_without_a_source_is_closed_by_its_own_route(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / PRD).write_text(self.text(PRD).replace(
            "A refund keeps the invoice. | planned | code |", "A refund keeps the invoice. | planned | config |"), encoding="utf-8")
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-03 src/features/orders/ship.py\n", encoding="utf-8")
        r = self.promote()
        self.assertNotIn("ERROR", r.stdout)
        self.assertNotIn("have no Source", r.stdout)
        self.assertFalse((self.p.root / "changes/001-disc").exists())
        self.assertIn("closed by their own route", r.stdout)
        self.assertIn("ORD-04", r.stdout)
        self.assertIn("pending code)* A refund keeps the invoice. | planned | config |", self.text(PRD))

    def test_a_table_without_a_change_via_column_keeps_its_superseded_id(self) -> None:
        write(self.p.root, "docs/prd/shop/06-glossary.md", "| ID | Term |\n|---|---|\n| ORD-01 | Order |\n")
        self.promote()
        self.assertIn("| ORD-01 | Order |", self.text("docs/prd/shop/06-glossary.md"))
        self.assertNotIn("| ORD-01 | An order", self.text(PRD))

    def test_an_amendment_file_and_a_trd_planned_section_are_warnings(self) -> None:
        write(self.p.root, "docs/prd/shop/05a-amendment-orders.md", PRD_TEXT.replace("ORD-0", "AMD-0"))
        r = self.promote()
        self.assertIn("amendment", r.stdout)

    def test_an_unknown_slug_is_an_error(self) -> None:
        r = self.p.py(PROMOTE, "nope")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("approved-rules.md", r.stdout + r.stderr)

    def source_case(self, deliveries: str, expect: dict[str, str]) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text(deliveries, encoding="utf-8")
        r = self.promote()
        self.assertNotIn("have no Source", r.stdout, r.stdout)
        prd = self.text(PRD)
        for rid, src in expect.items():
            self.assertRegex(prd, rf"\| {rid} \| [^|]*\| {re.escape(src)} \|")

    def test_source_with_a_colon_after_the_id_and_a_symbol(self) -> None:
        self.source_case("Source: ORD-02: src/a.py::cancel\nSource: ORD-03: src/b.py::ship\nSource: ORD-04: src/c.py::refund\n",
                         {"ORD-02": "src/a.py::cancel", "ORD-03": "src/b.py::ship", "ORD-04": "src/c.py::refund"})

    def test_source_with_an_id_list_sets_every_id(self) -> None:
        self.source_case("Source: ORD-02, ORD-03: src/a.py\nSource: ORD-04 src/c.py\n",
                         {"ORD-02": "src/a.py", "ORD-03": "src/a.py", "ORD-04": "src/c.py"})

    def test_source_with_an_id_range_expands_it(self) -> None:
        self.source_case("Source: ORD-02..04: src/a.py::run\n",
                         {"ORD-02": "src/a.py::run", "ORD-03": "src/a.py::run", "ORD-04": "src/a.py::run"})

    def test_source_with_several_paths_keeps_the_first(self) -> None:
        self.source_case("Source: ORD-02, ORD-03: src/a.py::x, src/b.py::y, ::z\nSource: ORD-04 -> src/c.py::w\n",
                         {"ORD-02": "src/a.py::x", "ORD-03": "src/a.py::x", "ORD-04": "src/c.py::w"})

    def test_the_old_one_id_form_still_works(self) -> None:
        self.source_case("Source: ORD-02 src/a.py::cancel\nSource: ORD-03 src/b.py\nSource: ORD-04 src/c.py\n",
                         {"ORD-02": "src/a.py::cancel", "ORD-03": "src/b.py", "ORD-04": "src/c.py"})

    def test_a_step5_changelog_entry_is_completed_not_duplicated(self) -> None:
        write(self.p.root, "docs/prd/CHANGELOG.md",
              "# CHANGELOG\n\n## disc (2026-10-04, Ana, changes/001-disc)\n\nReason: orders.\n\n### 05-orders.md\n\n"
              "**ORD-02** (rule text). Rewritten.\n\n    | ORD-02 | An unpaid order is cancelled after 30 s. |\n\n## older (2026-01-01, X, y)\n\nbody\n")
        self.promote()
        log = self.text("docs/prd/CHANGELOG.md")
        self.assertEqual(log.count("## disc ("), 1)
        self.assertEqual(log.count("**ORD-02**"), 1)
        self.assertIn("An unpaid order is cancelled after 30 s.", log)
        self.assertIn("An order is created only from a cart with at least one item.", log)
        self.assertIn("src/features/orders/order_service.py::cancel_unpaid", log)
        self.assertEqual(log.count("DEC-01"), 1)
        self.assertIn("## older", log)
        self.assertLess(log.index("## disc ("), log.index("## older"))

    def test_a_rerun_after_completion_changes_nothing(self) -> None:
        write(self.p.root, "docs/prd/CHANGELOG.md", "# CHANGELOG\n\n## disc (2026-10-04, Ana, changes/001-disc)\n\nReason: orders.\n")
        self.promote()
        before = self.text("docs/prd/CHANGELOG.md")
        self.promote()
        self.assertEqual(self.text("docs/prd/CHANGELOG.md"), before)

    def set_gate_config(self, **kv: str) -> None:
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        text = repo.read_text(encoding="utf-8")
        for key, value in kv.items():
            text = re.sub(rf"^\| {key} \|.*\|$", f"| {key} | {value} |", text, flags=re.M)
        repo.write_text(text, encoding="utf-8")

    def go_pt_br(self) -> None:
        self.set_gate_config(planned_source="planejado", pending_marker="pendente de código", language="Português")
        pt = ("approved 2026-10-04, pending code", "aprovada 2026-10-04, pendente de código")
        write(self.p.root, PRD, PRD_TEXT.replace(*pt).replace("| planned |", "| planejado |"))
        write(self.p.root, f"{STATE}/approved-rules.md", APPROVED.replace(*pt).replace("| planned |", "| planejado |"))
        (self.p.root / "docs/trd/orders.md").unlink()

    def test_pt_br_markers_come_from_repo_md(self) -> None:
        self.go_pt_br()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        prd = self.text(PRD)
        self.assertNotIn("pendente de código", prd, r.stdout)
        self.assertIn("| ORD-02 | An unpaid order is cancelled after 20 s. | src/a.py | config |", prd)

    def test_pt_br_planned_row_without_source_is_still_missing(self) -> None:
        self.go_pt_br()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ORD-04", r.stdout)

    def test_a_frontend_or_backend_rule_without_a_source_fails(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        for route in ("frontend", "backend"):
            write(self.p.root, PRD, PRD_TEXT.replace("A refund keeps the invoice. | planned | code |", f"A refund keeps the invoice. | planned | {route} |"))
            (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03: src/a.py" + chr(10), encoding="utf-8")
            r = self.promote()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("ORD-04", r.stdout)
            self.assertIn("--hold", r.stdout)

    def test_hold_leaves_the_row_planned_with_its_reason(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote("--hold", "ORD-04", "--reason", "front repo delivers it")
        self.assertEqual(r.returncode, 0, r.stdout)
        prd = self.text(PRD)
        self.assertIn("pending code)* A refund keeps the invoice. | planned | code |", prd)
        self.assertNotIn("pending code)* A paid order", prd)
        self.assertIn("held: ORD-04", r.stdout)
        self.assertIn("front repo delivers it", r.stdout)
        self.assertTrue((self.p.root / "changes/001-disc").is_dir())

    def test_a_second_promote_after_a_hold_extends_its_own_entry_once(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03: src/a.py" + chr(10), encoding="utf-8")
        self.promote("--hold", "ORD-04", "--reason", "front repo delivers it")
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout)
        log = self.text("docs/prd/CHANGELOG.md")
        self.assertEqual(log.count("## disc ("), 1, log)
        self.assertEqual(log.count("Decisions:"), 1, log)
        self.assertEqual(log.count("| DEC-01 |"), 1, log)
        self.assertNotIn("Held planned", log)
        self.assertRegex(log, r"Released: ORD-04")
        self.assertNotIn("pending code)* A refund", self.text(PRD))

    def test_an_entry_titled_with_the_change_folder_name_is_completed_not_duplicated(self) -> None:
        write(self.p.root, "docs/prd/CHANGELOG.md",
              "# CHANGELOG\n\n## 001-disc (2026-10-04, Ana, changes/001-disc)\n\nReason: orders.\n\n## older (2026-01-01, X, y)\n\nbody\n")
        self.promote()
        log = self.text("docs/prd/CHANGELOG.md")
        self.assertEqual(len(re.findall(r"^## (?:001-)?disc \(", log, re.M)), 1, log)
        self.assertEqual(log.count("DEC-01"), 1, log)

    def test_the_hold_note_lands_only_in_its_own_entry_even_after_an_older_promoted_one(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03: src/a.py" + chr(10), encoding="utf-8")
        write(self.p.root, "docs/prd/CHANGELOG.md",
              "# CHANGELOG\n\n## older (2026-01-01, X, y)\n\nSources: none set.\nPromoted: sources set.\n\n"
              "## disc (2026-10-04, Ana, changes/001-disc)\n\nReason: orders.\n")
        r = self.promote("--hold", "ORD-04", "--reason", "front repo delivers it")
        self.assertEqual(r.returncode, 0, r.stdout)
        log = self.text("docs/prd/CHANGELOG.md")
        older, own = log.split("## disc (")
        self.assertNotIn("Held planned", older)
        self.assertIn("Held planned: ORD-04", own)

    def test_decision_rows_from_rules_md_and_the_change_folder_are_copied_once(self) -> None:
        (self.p.root / STATE / "approved-rules.md").unlink()
        rules = APPROVED.replace("# Approved rules", "# Rules") + "## Decisions\n" + DECISIONS.split("\n", 2)[2]
        write(self.p.root, f"{STATE}/rules.md", rules)
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        self.promote()
        log = self.text("docs/prd/CHANGELOG.md")
        self.assertEqual(log.count("| DEC-01 |"), 1, log)
        self.assertEqual(log.count("Decisions:"), 1, log)

    def test_hold_requires_a_reason(self) -> None:
        r = self.promote("--hold", "ORD-04")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_the_state_rows_are_realigned_to_the_prd_text(self) -> None:
        (self.p.root / "docs/trd/orders.md").unlink()
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        self.promote()
        state = self.text(f"{STATE}/approved-rules.md")
        self.assertNotIn("pending code", state)
        self.assertIn("| ORD-02 | An unpaid order is cancelled after 20 s. | src/a.py | config |", state)
        self.assertIn("- ORD-02 (An unpaid order is cancelled after 30 s.)", state)

    def test_promote_reads_the_state_record_when_rules_md_exists(self) -> None:
        (self.p.root / STATE / "approved-rules.md").unlink()
        rules = APPROVED.replace("# Approved rules", "# Rules") + "## Decisions\n" + DECISIONS.split("\n", 2)[2]
        write(self.p.root, f"{STATE}/rules.md", rules)
        (self.p.root / "changes/001-disc/decisions.md").unlink()
        (self.p.root / "docs/trd/orders.md").unlink()
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "state record", check=True)
        (self.p.root / STATE / "deliveries.md").write_text("Source: ORD-02, ORD-03, ORD-04: src/a.py" + chr(10), encoding="utf-8")
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("| DEC-01 | How long to wait? | 20 s | 30 s | carts expire | ORD-02 |", self.text("docs/prd/CHANGELOG.md"))
        self.assertIn("| ORD-02 | An unpaid order is cancelled after 20 s. | src/a.py | config |", self.text(f"{STATE}/approved-rules.md"))
        self.assertNotIn("pending code", self.text(f"{STATE}/rules.md"))


ENTRY = """# CHANGELOG

## Cancel unpaid orders (2026-10-04, Ana, changes/001-disc)

Reason: unpaid orders are cancelled and shipped orders keep the invoice. IDs: ORD-02, ORD-03, ORD-04.
Conflicts: none.
Supersedes: ORD-01.

### shop/05-orders.md

**ORD-02** (whole row), rewritten.

    | ORD-02 | *(approved 2026-10-04, pending code)* An unpaid order is cancelled after 30 s. | planned | config |
"""

REPLY_DECISIONS = DECISIONS.replace("# Decisions · 001-disc\n", '# Decisions · 001-disc\n\nReply 1: "20 s is fine, | DEC-99 | not a row"\n')


class NewRoutePromoteTest(unittest.TestCase):
    """No approved-rules.md or rules.md in the state folder: the set comes from the CHANGELOG entry."""

    def setUp(self) -> None:
        self.p = Project()
        r = self.p.root
        shutil.copytree(KIT / "docs" / "templates", r / "docs" / "templates", dirs_exist_ok=True)
        write(r, PRD, PRD_TEXT)
        write(r, "docs/prd/CHANGELOG.md", ENTRY)
        write(r, f"{STATE}/deliveries.md", DELIVERIES + "Source: ORD-04 src/features/orders/refund.py\n")
        write(r, f"{STATE}/state.md", "state\n")
        write(r, "changes/001-disc/decisions.md", REPLY_DECISIONS)
        write(r, "changes/001-disc/plan.md", "plan\n")
        run(r, "git", "add", "-A", check=True)
        run(r, "git", "commit", "-q", "-m", "docs apply", check=True)

    def tearDown(self) -> None:
        self.p.close()

    def promote(self, *extra: str):
        return self.p.py(PROMOTE, "disc", *extra)

    def text(self, rel: str) -> str:
        return (self.p.root / rel).read_text(encoding="utf-8")

    def test_the_entry_drives_markers_sources_supersedes_decisions_and_archive(self) -> None:
        r = self.promote()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 approved, 1 superseded", r.stdout)
        prd = self.text(PRD)
        self.assertNotIn("pending code", prd)
        self.assertNotIn("| ORD-01 |", prd)
        self.assertIn("| ORD-02 | An unpaid order is cancelled after 20 s. | src/features/orders/order_service.py::cancel_unpaid | config |", prd)
        log = self.text("docs/prd/CHANGELOG.md")
        self.assertEqual(log.count("**ORD-02**"), 1, log)
        self.assertIn("**ORD-01** (whole row). Superseded.", log)
        self.assertIn("    | ORD-01 | An order is created only from a cart with at least one item.", log)
        self.assertIn("| DEC-01 | How long to wait? | 20 s | 30 s | carts expire | ORD-02 |", log)
        self.assertNotIn("DEC-99", log)
        self.assertIn("Promoted: sources set.", log)
        self.assertTrue((self.p.root / "changes/archive/001-disc").is_dir())
        self.assertFalse((self.p.root / STATE / "approved-rules.md").exists())
        self.assertIn("Rules: ORD-01, ORD-02, ORD-03, ORD-04", r.stdout)

    def test_dry_run_changes_nothing(self) -> None:
        before = self.text(PRD)
        r = self.promote("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.text(PRD), before)
        self.assertNotIn("Promoted", self.text("docs/prd/CHANGELOG.md"))

    def test_hold_keeps_the_row_planned_and_skips_the_archive(self) -> None:
        r = self.promote("--hold", "ORD-04", "--reason", "front repo delivers it")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("pending code)* A refund keeps the invoice.", self.text(PRD))
        self.assertTrue((self.p.root / "changes/001-disc").is_dir())
        self.assertIn("Held planned: ORD-04", self.text("docs/prd/CHANGELOG.md"))

    def test_a_delivered_rule_without_a_source_fails_without_changes(self) -> None:
        write(self.p.root, f"{STATE}/deliveries.md", "Source: ORD-02 src/a.py\n")
        before = self.text(PRD)
        r = self.promote()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no Source line", r.stdout)
        self.assertEqual(self.text(PRD), before)

    def test_an_id_of_the_entry_in_no_prd_file_is_a_clean_error(self) -> None:
        write(self.p.root, "docs/prd/CHANGELOG.md", ENTRY.replace("ORD-04.", "ORD-04, ORD-77."))
        r = self.promote()
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("ORD-77", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_no_entry_and_no_state_record_is_a_clean_error(self) -> None:
        write(self.p.root, "docs/prd/CHANGELOG.md", "# CHANGELOG\n")
        r = self.promote()
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("nothing to promote", r.stdout)

    def test_a_state_folder_with_approved_rules_is_still_the_old_route(self) -> None:
        write(self.p.root, f"{STATE}/approved-rules.md", APPROVED)
        write(self.p.root, "docs/prd/CHANGELOG.md", "# CHANGELOG\n")
        r = self.promote("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 approved, 1 superseded", r.stdout)


if __name__ == "__main__":
    unittest.main()

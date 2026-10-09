"""state_record: one record per change (rules.md, delta.md) and the legacy views rendered from it."""

import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_kit_scripts import KIT

sys.path.insert(0, str(KIT / ".claude/skills/prd-flow/scripts"))
import state_record as sr  # noqa: E402

RULES = """\
# Rules · disc · 2026-10-04 · Ana
Scope: short C5 outside a C5
## docs/prd/shop/05-orders.md
| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-02 | *(approved 2026-10-04, pending code)* Cancel after 20 s. | planned | config |
## Supersedes
- ORD-02 (Cancel after 30 s.)
## Rounds
| Round | Date | Summary |
|---|---|---|
| 1 | 2026-10-04 | first |
## Decisions
| ID | Question | Decision | Rejected alternative | Why | Rules |
|---|---|---|---|---|---|
| DEC-01 | How long? | 20 s | 30 s | carts expire | ORD-02 |
## Dimensions
| Dimension | State | Answer |
|---|---|---|
| D01 Goal | user | cancel |
Confirmed: Ana · 2026-10-04 · "ok"
"""


class StateRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name)
        (self.state / "rules.md").write_text(RULES, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_the_approved_view_keeps_rows_and_supersedes_and_drops_the_rest(self) -> None:
        text = sr.approved_text(self.state)
        self.assertTrue(text.startswith("# Approved rules · disc · 2026-10-04 · Ana"))
        self.assertIn("## docs/prd/shop/05-orders.md", text)
        self.assertIn("- ORD-02 (Cancel after 30 s.)", text)
        self.assertNotIn("Rounds", text)
        self.assertNotIn("Dimensions", text)
        self.assertNotIn("DEC-01", text)

    def test_the_interview_view_has_scope_dimensions_and_confirmed(self) -> None:
        text = sr.interview_text(self.state)
        self.assertIn("Scope: short C5 outside a C5", text)
        self.assertIn("## Dimensions", text)
        self.assertIn("| D01 Goal | user | cancel |", text)
        self.assertIn("Confirmed: Ana", text)
        self.assertNotIn("ORD-02", text)

    def test_decision_rows_come_from_the_record(self) -> None:
        self.assertEqual(sr.decision_rows(self.state, None), ["| DEC-01 | How long? | 20 s | 30 s | carts expire | ORD-02 |"])

    def test_without_rules_md_the_legacy_files_are_read(self) -> None:
        (self.state / "rules.md").unlink()
        self.assertIsNone(sr.approved_text(self.state))
        (self.state / "approved-rules.md").write_text("legacy", encoding="utf-8")
        (self.state / "interview.md").write_text("iv", encoding="utf-8")
        self.assertEqual(sr.approved_text(self.state), "legacy")
        self.assertEqual(sr.interview_text(self.state), "iv")

    def test_replacing_a_row_changes_it_in_place_and_never_duplicates(self) -> None:
        sr.replace_rows(self.state, {"ORD-02": "| ORD-02 | Cancel after 20 s. | src/a.py | config |"})
        text = (self.state / "rules.md").read_text(encoding="utf-8")
        self.assertEqual(sum(ln.startswith("| ORD-02 |") for ln in text.splitlines()), 1)
        self.assertIn("src/a.py", text)
        self.assertLess(text.index("src/a.py"), text.index("## Supersedes"))

    def test_upsert_row_appends_a_new_rule_under_its_file(self) -> None:
        sr.upsert_row(self.state, "docs/prd/shop/05-orders.md", "| ORD-09 | New. | planned | code |")
        text = (self.state / "rules.md").read_text(encoding="utf-8")
        self.assertLess(text.index("| ORD-09 |"), text.index("## Supersedes"))

    def test_add_round_appends_to_the_rounds_table(self) -> None:
        sr.add_round(self.state, 2, "2026-10-05", "second")
        text = (self.state / "rules.md").read_text(encoding="utf-8")
        self.assertIn("| 2 | 2026-10-05 | second |", text)
        self.assertLess(text.index("| 2 |"), text.index("## Decisions"))

    def test_delta_upserts_one_line_per_id_and_op(self) -> None:
        sr.append_delta(self.state, "ORD-02", "rewrite", "src/a.py", "20 s")
        sr.append_delta(self.state, "ORD-02", "rewrite", "src/b.py", "20 s again")
        text = (self.state / "delta.md").read_text(encoding="utf-8")
        self.assertEqual(sum(ln.startswith("| ORD-02 |") for ln in text.splitlines()), 1)
        self.assertIn("src/b.py", text)

    def test_render_views_writes_the_three_legacy_files(self) -> None:
        change = self.state / "change"
        change.mkdir()
        sr.render_views(self.state, change)
        self.assertIn("# Approved rules", (self.state / "approved-rules.md").read_text(encoding="utf-8"))
        self.assertIn("## Dimensions", (self.state / "interview.md").read_text(encoding="utf-8"))
        self.assertIn("DEC-01", (change / "decisions.md").read_text(encoding="utf-8"))

    def test_gate_interview_reads_the_rendered_view_when_only_rules_md_exists(self) -> None:
        import gate_core
        import gate_interview

        gate_core.errors.clear()
        gate_interview.check_interview(self.state / "approved-rules.md", self.state, {})
        text = chr(10).join(gate_core.errors)
        self.assertNotIn("not found", text)
        self.assertIn("without the dimension D02", text)
        gate_core.errors.clear()


if __name__ == "__main__":
    unittest.main()

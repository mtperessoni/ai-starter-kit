"""Round 1 fixes of the rule-as-data gate: G2 files and rows (R03), cited IDs (R04), modes (R05), D4 final (R06), gen_index (R07), G4 added only (R11)."""

import unittest

from tests.gate_report import full
from tests.test_gate_rule_as_data import GATE, ORDERS, SOURCE, row
from tests.test_gate_trd_sibling import commit
from tests.test_kit_scripts import Project, write

INDEXER = ".claude/skills/prd-flow/scripts/gen_index.py"
DASH = chr(0x2014)
HEAD = "## 06\n\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n"


class GateFixesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def gate(self, *args: str):
        r = self.p.py(GATE, *args)
        self.assertNotIn("Traceback", r.stderr)
        return r, full(self.p, r)

    def cite(self, rid: str) -> None:
        write(self.p.root, f"src/features/orders/tests/test_{rid.lower().replace('-', '_')}.py", f'"""{rid}."""\n')

    def test_r03_a_section_file_without_an_index_row_errors(self) -> None:
        write(self.p.root, "docs/prd/shop/06-more.md", HEAD + row("MOR-01", source=SOURCE))
        self.cite("MOR-01")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G2", r.stdout)
        self.assertIn("06-more.md", r.stdout)

    def test_r03_an_index_row_to_a_missing_file_errors(self) -> None:
        index = self.p.root / "docs/prd/INDEX.md"
        index.write_text(index.read_text(encoding="utf-8") + "| [09-gone.md](shop/09-gone.md) | Gone | GON-01 | |\n", encoding="utf-8", newline="\n")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G2", r.stdout)
        self.assertIn("09-gone.md", r.stdout)

    def test_r04_a_trd_row_citing_an_unknown_id_added_by_the_diff_errors(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\n| Rule | File |\n|---|---|\n| ORD-77 | `src/features/orders/order_service.py` |\n")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G8", r.stdout)
        self.assertIn("ORD-77", r.stdout)

    def test_r04_a_test_citing_an_unknown_id_added_by_the_diff_errors(self) -> None:
        write(self.p.root, "src/features/orders/tests/test_ghost.py", '"""ORD-88."""\n')
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G8", r.stdout)
        self.assertIn("ORD-88", r.stdout)

    def test_r04_known_ids_and_foreign_codes_are_not_errors(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\nORD-01 uses UTF-8 and SHA-256; I-99 is an invariant.\n")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_r05_docs_and_step_trd_do_not_error_on_removed_bookkeeping(self) -> None:
        for args in (("--docs", "orders", "--fresh"), ("--step", "trd"), ("--step", "prd")):
            r, report = self.gate(*args)
            self.assertEqual(r.returncode, 0, (args, r.stdout))
            for code in ("G7", "Q2"):
                self.assertNotIn(code, r.stdout, args)

    def test_r05_the_help_names_the_modes_with_the_six_errors(self) -> None:
        text = (self.p.root / GATE).read_text(encoding="utf-8")
        self.assertIn("six change errors", text)

    def test_r06_final_warns_on_an_existing_pending_marker(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + row("ORD-03", "A later rule. *(approved 2026-10-01, pending code)*", source="planned"), encoding="utf-8", newline="\n")
        self.p.py(GATE, "--fix")
        commit(self.p)
        r, report = self.gate("--final")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("ERROR G19", r.stdout)
        self.assertIn("WARNING G19", report)

    def test_r07_gen_index_handles_multi_segment_and_suffixed_ids(self) -> None:
        write(self.p.root, "docs/prd/shop/06-more.md", HEAD + row("ABC-DEF-01") + row("ABC-DEF-02") + row("ABC-DEF-03") + row("CNX-10") + row("CNX-10a"))
        index = self.p.root / "docs/prd/INDEX.md"
        index.write_text(index.read_text(encoding="utf-8") + "| [06-more.md](shop/06-more.md) | More | | |\n", encoding="utf-8", newline="\n")
        repo = str(self.p.root)
        self.assertEqual(self.p.py(INDEXER, "--repo", repo, "--check").returncode, 1)
        self.assertEqual(self.p.py(INDEXER, "--repo", repo).returncode, 0)
        cell = index.read_text(encoding="utf-8")
        self.assertIn("ABC-DEF-01..03", cell)
        self.assertIn("CNX-10a", cell)
        self.assertEqual(self.p.py(INDEXER, "--repo", repo, "--check").returncode, 0)

    def test_r07_check_agrees_with_the_gate_on_a_hand_written_cell(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + row("ORD-03"), encoding="utf-8", newline="\n")
        index = self.p.root / "docs/prd/INDEX.md"
        index.write_text(index.read_text(encoding="utf-8").replace("ORD-01..02", "ORD-01, ORD-02, ORD-03"), encoding="utf-8", newline="\n")
        r = self.p.py(INDEXER, "--repo", str(self.p.root), "--check")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_r11_an_existing_em_dash_does_not_fail_a_later_change(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("An order is created from a cart.", f"An order {DASH} from a cart."), encoding="utf-8", newline="\n")
        commit(self.p)
        r, report = self.gate("--base", "HEAD")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G4", r.stdout)


if __name__ == "__main__":
    unittest.main()

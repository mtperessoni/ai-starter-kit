"""prd_sweep.py: the deterministic sweep and functional proof of prd-flow (WF75)."""

import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "kit" / ".claude" / "skills" / "prd-flow" / "scripts" / "prd_sweep.py"
FIXTURE = HERE / "fixtures" / "sweep"


def sweep(*args: str, root: Path = FIXTURE) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )


def section(text: str, name: str) -> str:
    parts = text.split(f"## {name}\n", 1)
    return parts[1].split("\n## ", 1)[0] if len(parts) == 2 else ""


class SweepTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "sweep.md"
        start = time.time()
        cls.run_ = sweep("--ids", "ORD-01,ORD-02,ORD-03,ORD-04,SHP-01,ZZZ-99", "--terms", "shipping,cart", "--out", str(cls.out))
        cls.elapsed = time.time() - start
        cls.text = cls.out.read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_summary_is_short_and_exit_zero(self) -> None:
        self.assertEqual(self.run_.returncode, 0, self.run_.stderr)
        self.assertLessEqual(len(self.run_.stdout.strip().splitlines()), 6)
        self.assertIn(str(self.out), self.run_.stdout)

    def test_fast_and_bounded(self) -> None:
        self.assertLess(self.elapsed, 2.0)
        self.assertLessEqual(len(self.text.splitlines()), 200)
        self.assertNotIn(chr(0x2014), self.text)

    def test_rules_literal_row(self) -> None:
        rules = section(self.text, "Rules")
        self.assertIn("docs/prd/shop/05-orders.md", rules)
        self.assertIn("| ORD-01 | An order is created only from a cart with at least one item. |", rules)
        self.assertIn("ZZZ-99", rules)
        self.assertIn("not found", rules)

    def test_cited_by_excludes_own_row(self) -> None:
        cited = section(self.text, "Cited by")
        self.assertIn("06-shipping.md:6", cited)
        self.assertIn("Q-01", cited)
        self.assertNotIn("05-orders.md:5:", cited)

    def test_same_table_lists_others_with_80_chars(self) -> None:
        same = section(self.text, "Same table")
        self.assertIn("SHP-02", same)
        self.assertNotIn("Q-01", same)

    def test_candidates_use_index_and_terms(self) -> None:
        cand = section(self.text, "Candidates")
        self.assertIn("shop/06-shipping.md", cand)
        self.assertIn("SHP-01", cand)
        self.assertIn("ORD-01", cand)

    def test_unconditional_flags_numbers_and_absolute_words(self) -> None:
        unc = section(self.text, "Unconditional")
        self.assertIn("SHP-01", unc)
        self.assertIn("ORD-02", unc)
        self.assertNotIn("ORD-03", unc)

    def test_history_with_heading(self) -> None:
        hist = section(self.text, "History")
        self.assertIn("2026-03-01 orders limits", hist)
        self.assertIn("ORD-02", hist)

    def test_active_changes_skip_archive(self) -> None:
        active = section(self.text, "Active changes")
        self.assertIn("changes/010-free-shipping/plan.md", active)
        self.assertNotIn("archive", active)

    def test_tests_citing_id(self) -> None:
        tests = section(self.text, "Tests")
        self.assertIn("tests/test_orders.py", tests)

    def test_code_verdicts(self) -> None:
        code = section(self.text, "Code")
        lines = {line.split(":", 1)[0].strip("- "): line for line in code.splitlines() if line.startswith("- ")}
        self.assertIn("found", lines["ORD-01"])
        self.assertIn("src/checkout.py:", lines["ORD-01"])
        self.assertIn("not wired", lines["ORD-02"])
        self.assertIn("planned", lines["ORD-03"])
        self.assertIn("missing", lines["ORD-04"])
        self.assertIn("found", lines["SHP-01"])
        self.assertIn("F3: read src/orders.py::create_order", code)

    def test_pending_marker_row_with_example_column(self) -> None:
        res = sweep("--ids", "RET-01")
        rules = section(res.stdout, "Rules")
        self.assertIn("07-returns.md:5", rules)
        self.assertNotIn("not found", rules)
        self.assertIn("planned", section(res.stdout, "Code"))
        self.assertIn("RET-02", section(res.stdout, "Same table"))

    def test_own_row_excluded_from_cited_by(self) -> None:
        cited = section(sweep("--ids", "RET-01").stdout, "Cited by")
        self.assertNotIn("07-returns.md:5:", cited)

    def test_ignored_folder_not_walked(self) -> None:
        res = sweep("--ids", "RET-01")
        self.assertNotIn("node_modules", section(res.stdout, "Tests"))

    def test_stdout_when_no_out(self) -> None:
        res = sweep("--ids", "ORD-01")
        self.assertEqual(res.returncode, 0)
        self.assertIn("## Rules", res.stdout)

    def test_bad_arguments_exit_two(self) -> None:
        self.assertEqual(sweep().returncode, 2)

    def test_missing_index_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sweep("--ids", "ORD-01", root=Path(tmp)).returncode, 2)


if __name__ == "__main__":
    unittest.main()

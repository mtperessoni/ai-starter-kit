"""Rule-as-data gate: INDEX generated (S3), no HTML in the change gate (S4), six errors (S6), --history (S2), pending markers (D4)."""

import unittest

from tests.gate_report import full
from tests.test_gate_trd_sibling import commit
from tests.test_kit_scripts import Project, run, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
SOURCE = "src/features/orders/order_service.py"


def row(rid: str, text: str = "A new rule.", source: str = SOURCE, via: str = "code") -> str:
    return f"| {rid} | {text} | {source} | {via} |\n"


class RuleAsDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def append(self, line: str, rel: str = ORDERS) -> None:
        path = self.p.root / rel
        path.write_text(path.read_text(encoding="utf-8") + line, encoding="utf-8", newline="\n")

    def cite(self, rid: str) -> None:
        write(self.p.root, f"src/features/orders/tests/test_{rid.lower().replace('-', '_')}.py", f'"""{rid}."""\n')

    def gate(self, *args: str):
        r = self.p.py(GATE, *args)
        self.assertNotIn("Traceback", r.stderr)
        return r, full(self.p, r)

    def test_a_clean_change_passes(self) -> None:
        r, _ = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_s3_a_stale_index_errors_and_fix_repairs_it(self) -> None:
        self.append(row("ORD-03"))
        self.cite("ORD-03")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G2", r.stdout)
        self.assertIn("ORD-01..03", r.stdout)
        fixed, _ = self.gate("--fix")
        self.assertEqual(fixed.returncode, 0, fixed.stdout)
        self.assertIn("ORD-01..03", (self.p.root / "docs/prd/INDEX.md").read_text(encoding="utf-8"))
        again, _ = self.gate()
        self.assertEqual(again.returncode, 0, again.stdout)

    def test_s3_gen_index_check_reports_and_writes(self) -> None:
        self.append(row("ORD-03"))
        script = ".claude/skills/prd-flow/scripts/gen_index.py"
        stale = self.p.py(script, "--repo", str(self.p.root), "--check")
        self.assertEqual(stale.returncode, 1, stale.stdout)
        self.assertEqual(self.p.py(script, "--repo", str(self.p.root)).returncode, 0)
        self.assertEqual(self.p.py(script, "--repo", str(self.p.root), "--check").returncode, 0)

    def test_s4_an_html_problem_does_not_fail_the_change_gate(self) -> None:
        write(self.p.root, "docs/prd/prd.html", "<html>" + chr(0x2014) + " stale</html>\n")
        for args in ((), ("--step", "prd"), ("--docs", "x", "--fresh")):
            r, report = self.gate(*args)
            self.assertEqual(r.returncode, 0, (args, r.stdout))
            for code in ("G5", "G29", "G32"):
                self.assertNotIn(code, report, args)

    def test_s4_the_docs_html_check_still_exists(self) -> None:
        r, _ = self.gate("--html")
        self.assertIn("G29", r.stdout)

    def test_s6_g1_duplicate_id(self) -> None:
        write(self.p.root, "docs/prd/shop/06-more.md", "## 06\n\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n" + row("ORD-01"))
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERROR G1", r.stdout)

    def test_s6_g3_incomplete_row(self) -> None:
        self.append(row("ORD-03", source=""))
        self.cite("ORD-03")
        r, _ = self.gate("--fix")
        self.assertIn("ERROR G3", r.stdout)

    def test_s6_g8_planned_cites_a_missing_id(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\n## Planned\n\nORD-99 comes later.\n")
        r, _ = self.gate()
        self.assertIn("ERROR G8", r.stdout)

    def test_s6_g12_changed_rule_needs_a_test(self) -> None:
        self.append(row("ORD-03"))
        self.p.py(GATE, "--fix")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G12", r.stdout)
        self.assertIn("ORD-03", r.stdout)
        self.cite("ORD-03")
        ok, _ = self.gate()
        self.assertEqual(ok.returncode, 0, ok.stdout)

    def test_s6_g12_an_unchanged_untested_rule_is_not_an_error(self) -> None:
        r, _ = self.gate()
        self.assertNotIn("ORD-02", r.stdout)

    def test_s6_g4_em_dash_added(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("An order is created from a cart.", "An order " + chr(0x2014) + " from a cart."), encoding="utf-8")
        r, _ = self.gate()
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERROR G4", r.stdout)

    def test_s6_g7_a_reworded_rule_needs_no_changelog_line(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("at least one item", "two items"), encoding="utf-8")
        r, report = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G7", report)

    def test_s6_g7_a_removed_rule_needs_no_changelog_line(self) -> None:
        path = self.p.root / ORDERS
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        path.write_text("".join(x for x in lines if not x.startswith("| ORD-02")), encoding="utf-8")
        self.p.py(GATE, "--fix")
        r, report = self.gate()
        self.assertNotIn("G7", report)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_s6_g23_and_g24_are_warnings_in_the_change_gate(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\nSee `src/features/orders/ghost_file.py`.\n")
        commit(self.p)
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\nSee `src/features/orders/ghost_file.py` and `src/nowhere/x.py`.\n")
        r, report = self.gate("--docs", "orders", "--fresh")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("ERROR G23", r.stdout)
        self.assertIn("WARNING G23", report)
        strict, _ = self.gate("--trd")
        self.assertIn("ERROR G23", strict.stdout)

    def test_s6_g28_is_a_warning_in_the_change_gate(self) -> None:
        sibling = self.p.root / "other/shop"
        write(self.p.root, "other/shop/a.md", "one\n")
        write(self.p.root, "docs/prd/shop/a.md", "two\n")
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        text = repo.read_text(encoding="utf-8")
        marker = "| PRD folder |"
        self.assertIn(marker, text)
        head, tail = text.split(marker, 1)
        repo.write_text(head + "| `docs/prd/shop` | `" + sibling.as_posix() + "` | here |\n" + marker + tail, encoding="utf-8")
        r, report = self.gate("--step", "prd")
        self.assertNotIn("ERROR G28", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G28", report)
        strict, _ = self.gate("--sibling")
        self.assertIn("ERROR G28", strict.stdout)

    def test_s2_history_lists_commits_that_touched_the_row_or_name_it(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8").replace("at least one item", "two items"), encoding="utf-8")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "feat(orders): raise the minimum\n\nRequest: raise the minimum items\nDecided: 1a two items (rejected: three)\nAssumed: carts are never empty\nRules: ORD-01", check=True)
        write(self.p.root, SOURCE, '"""ORD-01, ORD-02: orders."""\n\n\ndef create_order(cart):\n    return list(cart)\n')
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "fix(orders): copy the cart\n\nRules: ORD-01, ORD-05", check=True)
        path.write_text(path.read_text(encoding="utf-8").replace("payment timeout", "grace period"), encoding="utf-8")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "feat(orders): grace period\n\nRequest: rename the timeout", check=True)
        r = self.p.py(GATE, "--history", "ORD-01")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        self.assertIn("fix(orders): copy the cart", out)
        self.assertIn("feat(orders): raise the minimum", out)
        self.assertLess(out.index("copy the cart"), out.index("raise the minimum"))
        self.assertNotIn("grace period", out)
        self.assertIn("Request: raise the minimum items", out)
        self.assertIn("Decided: 1a two items (rejected: three)", out)
        self.assertIn("Assumed: carts are never empty", out)

    def test_d4_an_existing_pending_marker_is_valid(self) -> None:
        self.append(row("ORD-03", "A later rule. *(approved 2026-10-01, pending code)*", source="planned"))
        self.p.py(GATE, "--fix")
        commit(self.p)
        r, report = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("D4", report)

    def test_d4_a_marker_added_by_the_diff_is_a_warning(self) -> None:
        self.append(row("ORD-03", "A later rule. *(approved 2026-10-01, pending code)*", source="planned"))
        self.p.py(GATE, "--fix")
        r, report = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING D4", report)

    def test_d4_a_planned_trd_section_added_by_the_diff_is_a_warning(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\n## Planned\n\nORD-01 moves later.\n")
        r, report = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING D4", report)


if __name__ == "__main__":
    unittest.main()

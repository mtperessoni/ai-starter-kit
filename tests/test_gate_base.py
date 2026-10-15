"""gate.py base resolver, marker-only edits, G23 untracked files, G31, error fixes and separate caps."""

import unittest

from tests.test_kit_scripts import Project, run, write
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
ARTIFACT = ".claude/prd-flow/state/_gate/last-step-trd.txt"
MARKER = " *(approved 2026-10-07, pending code)*"
DASH = chr(0x2014)


def hand(p: Project) -> None:
    repo = p.root / ".claude/skills/prd-flow/repo.md"
    repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")
    run(p.root, "git", "commit", "-qam", "hand", check=True)


def edit(p: Project, rel: str, old: str, new: str) -> None:
    path = p.root / rel
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8", newline="\n")


class BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        hand(self.p)

    def tearDown(self) -> None:
        self.p.close()

    def test_a_missing_base_ref_is_an_error_with_a_fix(self) -> None:
        r = self.p.py(GATE, "--base", "no-such-ref")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G0", r.stdout)
        self.assertIn("; fix: ", r.stdout)

    def test_without_origin_the_local_base_branch_is_used(self) -> None:
        run(self.p.root, "git", "checkout", "-q", "-b", "feat", check=True)
        write(self.p.root, "docs/trd/orders.md", "# T\n\nThe order rule ORD-99 lives here.\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-qm", "trd", check=True)
        r = self.p.py(GATE)
        self.assertIn("ERROR G8", r.stdout)
        self.assertNotIn("no base", r.stdout)

    def test_without_any_base_it_warns_that_results_change_after_commit(self) -> None:
        run(self.p.root, "git", "branch", "-m", "trunk", check=True)
        r = self.p.py(GATE)
        self.assertIn("WARNING G0 no base", full(self.p, r))
        self.assertIn("results change after commit", full(self.p, r))
        self.assertEqual(full(self.p, r).count("WARNING G0"), 1, full(self.p, r))


class ChangelogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        hand(self.p)
        run(self.p.root, "git", "checkout", "-q", "-b", "feat", check=True)

    def tearDown(self) -> None:
        self.p.close()

    def test_a_marker_only_change_needs_no_changelog(self) -> None:
        edit(self.p, ORDERS, "| ORD-01 | An order", f"| ORD-01 |{MARKER} An order")
        run(self.p.root, "git", "commit", "-qam", "approve", check=True)
        edit(self.p, ORDERS, MARKER, "")
        r = self.p.py(GATE)
        self.assertNotIn("G7", r.stdout)

    def test_a_reword_needs_no_changelog_line_the_changelog_is_frozen(self) -> None:
        edit(self.p, ORDERS, "at least one item", "two items")
        r = self.p.py(GATE)
        self.assertNotIn("G7", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_unrelated_histories_warn_instead_of_silently_using_head(self) -> None:
        run(self.p.root, "git", "checkout", "-q", "--orphan", "orphan", check=True)
        run(self.p.root, "git", "commit", "-qm", "orphan", check=True)
        r = self.p.py(GATE)
        self.assertIn("WARNING G0 no merge-base", full(self.p, r))


class UntrackedTest(unittest.TestCase):
    def test_g23_accepts_an_untracked_source_file(self) -> None:
        p = Project()
        try:
            hand(p)
            write(p.root, "src/features/orders/fresh.py", "x = 1\n")
            trd = "# T\n\n| File | Role |\n|---|---|\n| `src/features/orders/fresh.py` | new |\n| `src/features/orders/gone.py` | gone |\n"
            write(p.root, "docs/trd/orders.md", trd)
            r = p.py(GATE, "--trd")
            report = full(p, r)
            self.assertNotIn("fresh.py", report)
            self.assertIn("WARNING G23", report)
            self.assertEqual(r.returncode, 0, r.stdout)
        finally:
            p.close()


class FixAndCapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        hand(self.p)

    def tearDown(self) -> None:
        self.p.close()

    def test_every_error_line_ends_with_a_fix(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + "\n| ORD-01 | A repeated ID | `x` | code |\n", encoding="utf-8", newline="\n")
        write(self.p.root, "docs/trd/orders.md", "# T\n\nThe order rule ORD-99 lives here.\n")
        r = self.p.py(GATE, "--step", "trd")
        errors = [x for x in r.stdout.splitlines() if x.startswith("ERROR")]
        self.assertGreaterEqual(len(errors), 2, r.stdout)
        for line in errors:
            self.assertEqual(line.count("; fix: "), 1, line)

    def test_errors_and_warnings_have_separate_caps_and_more_lines(self) -> None:
        lines = "".join(f"The order rule ORD-{100 + i} lives here.\n" for i in range(20))
        write(self.p.root, "docs/trd/many.md", "# T\n\n" + lines)
        for i in range(13):
            write(self.p.root, f"docs/trd/gone{i}.md", f"# T\n\n| File | Role |\n|---|---|\n| `src/nowhere/m{i}.py` | gone |\n")
        r = self.p.py(GATE, "--step", "trd")
        lines = r.stdout.splitlines()
        self.assertEqual(sum(1 for x in lines if x.startswith("ERROR")), 15, r.stdout)
        self.assertEqual(sum(1 for x in lines if x.startswith("WARNING")), 0, r.stdout)
        self.assertIn(f"... 5 more errors, see {ARTIFACT}", lines)
        self.assertEqual(lines[-1], f"warnings: 13 (see {ARTIFACT})")
        self.assertEqual(sum(1 for x in full(self.p, r).splitlines() if x.startswith("WARNING")), 13)

    def test_an_untouched_trd_file_with_a_missing_path_is_earlier_drift_and_never_an_error(self) -> None:
        write(self.p.root, "docs/trd/old.md", "# T\n\n| File | Role |\n|---|---|\n| `src/nowhere/other.py` | gone |\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-qm", "trd", check=True)
        r = self.p.py(GATE, "--step", "trd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("ERROR", r.stdout)
        self.assertIn("WARNING G23 earlier drift", full(self.p, r))


if __name__ == "__main__":
    unittest.main()

"""gate.py --status, the stdout shape of a run with warnings, and older adapters."""

import unittest

from tests.test_kit_scripts import Project
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"


class StatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        path = self.p.root / ORDERS
        text = path.read_text(encoding="utf-8")
        old = "(`OrderConfig.timeout`). | src/features/orders/order_service.py"
        path.write_text(text.replace(old, "(`OrderConfig.timeout`). *(proposed)* | planned"), encoding="utf-8", newline="\n")

    def tearDown(self) -> None:
        self.p.close()

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


class WarningsLineTest(unittest.TestCase):
    def test_stdout_is_the_errors_and_one_warnings_line(self) -> None:
        p = Project()
        try:
            write_trd = p.root / "docs/trd/orders.md"
            write_trd.parent.mkdir(parents=True, exist_ok=True)
            write_trd.write_text("# TRD\n\n## Planned\n\nORD-01 moves later.\n", encoding="utf-8", newline="\n")
            r = p.py(GATE, "--base", "HEAD")
            self.assertNotIn("WARNING", r.stdout)
            self.assertRegex(r.stdout.strip().splitlines()[-1], r"^warnings: [1-9]\d* \(see \.claude/prd-flow/state/_gate/last-default\.txt\)$")
            self.assertIn("WARNING D4", full(p, r))
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

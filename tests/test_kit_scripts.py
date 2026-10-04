"""End-to-end tests of the kit scripts against a throwaway project built from the payload."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1] / "kit"
PY = sys.executable


def find_bash() -> str | None:
    candidates = [shutil.which("bash"), r"C:\Program Files\Git\bin\bash.exe"]
    for c in candidates:
        if c and Path(c).exists() and "system32" not in c.lower():
            return c
    return None


BASH = find_bash()

SECTION = """\
## 05. Step 1 · Orders

An order is created from a cart.

| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-01 | An order is created only from a cart with at least one item. | src/features/orders/order_service.py::create_order | code |
| ORD-02 | An unpaid order is cancelled after the payment timeout (`OrderConfig.timeout`). | src/features/orders/order_service.py | config |
"""

INDEX = """\
# PRD index

## PRD 1 · Shop
| File | Section | IDs | TRD |
|---|---|---|---|
| [05-orders.md](shop/05-orders.md) | Step 1 · Orders | ORD-01..02 | |
"""

HTML = """\
<html><body>
<table class="rules"><tbody>
<tr data-via="code"><td>ORD-01</td><td>An order is created only from a cart with at least one item.</td><td>x</td></tr>
<tr data-via="config"><td>ORD-02</td><td>An unpaid order is cancelled after the payment timeout (<code>OrderConfig.timeout</code>).</td><td>x</td></tr>
</tbody></table>
</body></html>
"""


def run(cwd: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    result = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"{args} failed:\n{result.stdout}\n{result.stderr}")
    return result


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8", newline="\n")
    return path


class Project:
    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(KIT / "scripts", self.root / "scripts")
        shutil.copytree(KIT / ".claude", self.root / ".claude")
        config = json.loads((KIT / "ai-kit.json").read_text(encoding="utf-8"))
        config["code_extensions"] = [".py"]
        config["tests"]["runner"] = f'"{PY}" -c "print(\'FAILED fake::test_a\'); print(\'1 failed\')" {{files}}'
        write(self.root, "ai-kit.json", json.dumps(config, indent=2))
        write(self.root, "src/features/orders/CLAUDE.md", "# features/orders\n\nTRD: docs/trd/orders.md\n")
        write(self.root, "src/features/orders/order_service.py", '"""ORD-01, ORD-02: orders."""\n\n\ndef create_order(cart):\n    return cart\n')
        write(self.root, "src/features/orders/tests/test_order_service.py", '"""ORD-01."""\nfrom features.orders.order_service import create_order\n')
        write(self.root, "src/features/billing/CLAUDE.md", "# features/billing\n")
        write(self.root, "src/features/billing/invoice.py", '"""BIL-01: invoices."""\nfrom features.orders.order_service import create_order\n')
        write(self.root, "src/features/billing/tests/test_invoice.py", '"""BIL-01."""\nimport features.billing.invoice\n')
        write(self.root, "docs/prd/INDEX.md", INDEX)
        write(self.root, "docs/prd/CHANGELOG.md", "# CHANGELOG\n")
        write(self.root, "docs/prd/shop/05-orders.md", SECTION)
        write(self.root, "docs/prd/prd.html", HTML)
        write(self.root, "docs/trd/invariants.md", "| ID | Rule | Proof |\n|---|---|---|\n| I-01 | No em dash | gate |\n")
        run(self.root, "git", "init", "-q", "-b", "main", check=True)
        run(self.root, "git", "add", "-A", check=True)
        run(self.root, "git", "commit", "-q", "-m", "init", check=True)

    def py(self, *args: str) -> subprocess.CompletedProcess:
        return run(self.root, PY, *args)

    def close(self) -> None:
        self.tmp.cleanup()


class GateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.gate = ".claude/skills/prd-gate/scripts/gate.py"

    def tearDown(self) -> None:
        self.p.close()

    def test_a_consistent_prd_passes(self) -> None:
        r = self.p.py(self.gate)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("2 rules", r.stdout)

    def test_rewording_a_rule_without_changelog_fails(self) -> None:
        section = self.p.root / "docs/prd/shop/05-orders.md"
        section.write_text(section.read_text(encoding="utf-8").replace("at least one item", "two items"), encoding="utf-8")
        r = self.p.py(self.gate)
        self.assertEqual(r.returncode, 1)
        self.assertIn("G7", r.stdout)

    def test_markdown_and_html_must_say_the_same(self) -> None:
        html = self.p.root / "docs/prd/prd.html"
        html.write_text(html.read_text(encoding="utf-8").replace("at least one item", "one item"), encoding="utf-8")
        section = self.p.root / "docs/prd/shop/05-orders.md"
        section.write_text(section.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        changelog = self.p.root / "docs/prd/CHANGELOG.md"
        changelog.write_text("# CHANGELOG\n\nnote\n", encoding="utf-8")
        section.write_text(section.read_text(encoding="utf-8").replace("ORD-02 | An unpaid", "ORD-02 | Then an unpaid"), encoding="utf-8")
        r = self.p.py(self.gate)
        self.assertIn("G6", r.stdout)

    def test_em_dash_is_rejected(self) -> None:
        section = self.p.root / "docs/prd/shop/05-orders.md"
        section.write_text(section.read_text(encoding="utf-8") + "\nA note " + chr(0x2014) + " here.\n", encoding="utf-8")
        r = self.p.py(self.gate)
        self.assertEqual(r.returncode, 1)
        self.assertIn("G4", r.stdout)

    def test_a_pack_must_copy_rules_literally(self) -> None:
        pack = write(self.p.root, "pack.md", """\
            # Pack · t
            Base: abc
            ## Rules
            ### docs/prd/shop/05-orders.md
            | ORD-01 | An order needs items. |
            ## TRD
            ## Invariants
            - I-01 x
            ## Principles
            ## Divergences
            ## Pre-interview
            """)
        r = self.p.py(self.gate, "--pack", str(pack))
        self.assertIn("paraphrase", r.stdout)

    def test_a_plan_task_needs_owns(self) -> None:
        plan = write(self.p.root, "plan.md", "## Plan execution rules\n\n### T01 · do\nModel: sonnet\nReviewer: none\n")
        r = self.p.py(self.gate, "--plan", str(plan))
        self.assertEqual(r.returncode, 1)
        self.assertIn("P2", r.stdout)


class RatchetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_a_clean_tree_passes(self) -> None:
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_long_module_fails_until_allowlisted_and_the_entry_only_shrinks(self) -> None:
        big = write(self.p.root, "src/features/orders/order_report.py", '"""ORD-01."""\n' + "x = 1\n" * 520)
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("order_report.py", r.stdout)
        init = json.loads(self.p.py("scripts/ratchet.py", "--init").stdout)
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["allowlist"] = init
        config_path.write_text(json.dumps(config), encoding="utf-8")
        self.assertEqual(self.p.py("scripts/ratchet.py").returncode, 0)
        big.write_text('"""ORD-01."""\n' + "x = 1\n" * 510, encoding="utf-8")
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("lower the entry", r.stdout)

    def test_generic_names_and_missing_ids_and_maps_fail(self) -> None:
        write(self.p.root, "src/features/orders/utils.py", '"""ORD-01."""\n')
        write(self.p.root, "src/features/orders/pricing.py", "def price():\n    return 1\n")
        write(self.p.root, "src/features/shipping/rates.py", '"""SHP-01."""\n')
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertIn("banned_names", out)
        self.assertIn("no_prd_id", out)
        self.assertIn("no_feature_map", out)


class RelatedTestsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_mirror_and_importers_are_found(self) -> None:
        r = self.p.py("scripts/related_tests.py", "src/features/orders/order_service.py")
        found = set(r.stdout.split())
        self.assertIn("src/features/orders/tests/test_order_service.py", found)
        self.assertNotIn("src/features/billing/tests/test_invoice.py", found)

    def test_a_changed_test_is_its_own_related_test(self) -> None:
        r = self.p.py("scripts/related_tests.py", "src/features/billing/tests/test_invoice.py")
        self.assertEqual(r.stdout.split(), ["src/features/billing/tests/test_invoice.py"])

    def test_run_prints_only_failures_and_the_summary(self) -> None:
        r = self.p.py("scripts/related_tests.py", "src/features/orders/order_service.py", "--run")
        lines = r.stdout.splitlines()
        self.assertIn("FAILED fake::test_a", lines)
        self.assertIn("1 failed", lines)
        self.assertTrue((self.p.root / ".claude/prd-gate/state/_tests/related.log").exists())


class NewFailuresTest(unittest.TestCase):
    def test_only_failures_outside_the_baseline_count(self) -> None:
        p = Project()
        try:
            write(p.root, "base.log", "FAILED a::one\nFAILED a::two\n2 failed\n")
            write(p.root, "final.log", "FAILED a::two\nFAILED b::three\n2 failed\n")
            baseline = p.py("scripts/new_failures.py", "--extract", "base.log").stdout
            write(p.root, "baseline.txt", baseline)
            r = p.py("scripts/new_failures.py", "baseline.txt", "final.log")
            self.assertEqual(r.returncode, 1)
            self.assertIn("NEW b::three", r.stdout)
            self.assertNotIn("a::two", r.stdout.replace("baseline", ""))
        finally:
            p.close()


@unittest.skipUnless(BASH, "bash not available")
class GatesShTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_related_runs_the_ratchet_then_only_the_related_tests(self) -> None:
        r = run(self.p.root, BASH, "scripts/gates.sh", "related", "src/features/orders/order_service.py")
        self.assertIn("ratchet: 0 problem(s)", r.stdout, r.stdout + r.stderr)
        self.assertIn("FAILED fake::test_a", r.stdout)

    def test_an_unknown_target_prints_usage(self) -> None:
        r = run(self.p.root, BASH, "scripts/gates.sh", "nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)


class MoveLinesTest(unittest.TestCase):
    def test_a_block_moves_without_retyping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "a.py", "one\ntwo\nthree\nfour\n")
            write(root, "b.py", "head\n")
            r = run(root, PY, str(KIT / "scripts" / "move_lines.py"), "a.py", "2", "3", "b.py")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual((root / "a.py").read_text(encoding="utf-8"), "one\nfour\n")
            self.assertEqual((root / "b.py").read_text(encoding="utf-8"), "head\ntwo\nthree\n")


if __name__ == "__main__":
    unittest.main()

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
        # a detached auto gc or maintenance writes into .git while cleanup removes it (Directory not empty in CI)
        run(self.root, "git", "config", "gc.auto", "0", check=True)
        run(self.root, "git", "config", "maintenance.auto", "false", check=True)
        run(self.root, "git", "add", "-A", check=True)
        run(self.root, "git", "commit", "-q", "-m", "init", check=True)

    def py(self, *args: str) -> subprocess.CompletedProcess:
        return run(self.root, PY, *args)

    def close(self) -> None:
        self.tmp.cleanup()


class GateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.gate = ".claude/skills/prd-flow/scripts/gate.py"
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")

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

    def test_open_questions_table_gets_no_change_via_warning(self) -> None:
        section = self.p.root / "docs/prd/shop/05-orders.md"
        section.write_text(
            section.read_text(encoding="utf-8")
            + "\n| ID | Question | Default adopted | Blocks |\n|---|---|---|---|\n"
            + "| Q1-01 | Refund window? | 30 days | ORD-02 |\n"
            + "\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n"
            + "| ORD-03 | Bad via row. | src/x.py | magic |\n",
            encoding="utf-8",
        )
        r = self.p.py(self.gate, "--base", "HEAD")
        self.assertNotIn("Q1-01: Change via", r.stdout)
        self.assertIn("ORD-03: Change via", r.stdout)

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

    def skip_checks(self, names: list[str]) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["ratchet"] = {"skip": names}
        config_path.write_text(json.dumps(config), encoding="utf-8")

    def test_a_skipped_check_reports_nothing_and_needs_no_allowlist(self) -> None:
        write(self.p.root, "src/features/orders/order_report.py", '"""ORD-01."""\n' + "x = 1\n" * 520)
        write(self.p.root, "src/features/orders/utils.py", '"""ORD-01."""\n')
        self.skip_checks(["long_modules", "generic_names"])
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        init = json.loads(self.p.py("scripts/ratchet.py", "--init").stdout)
        self.assertNotIn("long_modules", init)
        self.assertNotIn("banned_names", init)

    def test_a_check_that_is_not_skipped_still_fails(self) -> None:
        write(self.p.root, "src/features/orders/order_report.py", '"""ORD-01."""\n' + "x = 1\n" * 520)
        self.skip_checks(["long_tests"])
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("order_report.py", r.stdout)

    def test_an_unknown_skip_name_is_reported(self) -> None:
        self.skip_checks(["nope"])
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ratchet.skip: unknown check nope", r.stdout)

    def test_generic_names_and_missing_ids_and_maps_fail(self) -> None:
        write(self.p.root, "src/features/orders/utils.py", '"""ORD-01."""\n')
        write(self.p.root, "src/features/orders/pricing.py", "def price():\n    return 1\n")
        write(self.p.root, "src/features/shipping/rates.py", '"""SHP-01."""\n')
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertIn("banned_names", out)
        self.assertIn("no_prd_id", out)
        self.assertIn("no_feature_map", out)

    def configure(self, **keys) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config.update(keys)
        config_path.write_text(json.dumps(config), encoding="utf-8")

    def test_a_layer_layout_checks_its_declared_areas_and_map_dirs(self) -> None:
        self.configure(layout="layer", areas={"orders": ["src/services/order_*.py", "src/controllers/order_*.py"]},
                       map_dirs=["src/services"])
        write(self.p.root, "src/services/order_totals.py", "def total():\n    return 1\n")
        write(self.p.root, "src/services/report_export.py", "def export():\n    return 1\n")
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertIn("no_prd_id: src/services/order_totals.py", out)
        self.assertNotIn("report_export.py", out)
        self.assertIn("no_feature_map: src/services", out)
        write(self.p.root, "src/services/order_totals.py", '"""ORD-01: order totals."""\n')
        write(self.p.root, "src/services/CLAUDE.md", "# services\n\n| Area | Files | TRD |\n")
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_declared_area_or_map_dir_that_matches_nothing_fails(self) -> None:
        self.configure(layout="layer", areas={"ghost": ["src/ghost/*.py"]}, map_dirs=["src/nowhere"])
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("areas: ghost matches no file", r.stdout)
        self.assertIn("map_dirs: src/nowhere does not exist", r.stdout)

    def test_test_patterns_are_case_sensitive_on_every_os(self) -> None:
        write(self.p.root, "src/features/orders/latest.py", "x = 1\n")
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertIn("no_prd_id: src/features/orders/latest.py", out)

    def test_a_crowded_folder_fails(self) -> None:
        for i in range(21):
            write(self.p.root, f"src/legacy/report_part_{i}.py", "x = 1\n")
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertIn("crowded_dirs: src/legacy has 21", out)

    def test_a_generated_file_needs_its_marker_and_skips_the_other_checks(self) -> None:
        self.configure(generated_patterns=["src/gen/**"])
        write(self.p.root, "src/gen/client_models.py", "x = 1\n" * 600)
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertIn("generated_without_marker: src/gen/client_models.py", out)
        self.assertNotIn("long_modules", out)
        write(self.p.root, "src/gen/client_models.py", "# Code generated by openapi. DO NOT EDIT.\n" + "x = 1\n" * 600)
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_generator_header_or_a_project_marker_counts_as_generated(self) -> None:
        self.configure(generated_patterns=["src/gen/**"])
        write(self.p.root, "src/gen/0001_initial.py", "# Generated by Django 5.0 on 2026-01-01\nx = 1\n")
        write(self.p.root, "src/gen/api_client.py", "# built by tool-x, hands off\nx = 1\n")
        out = self.p.py("scripts/ratchet.py").stdout
        self.assertNotIn("0001_initial.py", out)
        self.assertIn("generated_without_marker: src/gen/api_client.py", out)
        self.configure(generated_marker="hands off")
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_config_without_the_layout_keys_still_passes(self) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for key in ("layout", "areas", "map_dirs"):
            config.pop(key, None)
        config_path.write_text(json.dumps(config), encoding="utf-8")
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)


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

    def test_a_dotted_module_finds_its_mirror_spec(self) -> None:
        write(self.p.root, "src/services/order.service.py", "def total():\n    return 1\n")
        write(self.p.root, "src/services/order.service.spec.py", "def test_total():\n    assert True\n")
        r = self.p.py("scripts/related_tests.py", "src/services/order.service.py")
        self.assertIn("src/services/order.service.spec.py", r.stdout.split())

    def configure(self, **tests) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["tests"].update(tests)
        config["code_extensions"] = [".py", ".java", ".rb", ".php"]
        config_path.write_text(json.dumps(config), encoding="utf-8")

    def test_a_mirror_in_another_tree_with_a_suffix_is_found(self) -> None:
        self.configure()
        write(self.p.root, "src/main/java/shop/OrderService.java", "class OrderService {}\n")
        write(self.p.root, "src/test/java/shop/OrderServiceTest.java", "class OrderServiceTest {}\n")
        r = self.p.py("scripts/related_tests.py", "src/main/java/shop/OrderService.java")
        self.assertIn("src/test/java/shop/OrderServiceTest.java", r.stdout.split())

    def test_a_test_that_only_names_the_symbol_is_related_when_match_symbol_is_on(self) -> None:
        write(self.p.root, "app/services/order_service.rb", "class OrderService\nend\n")
        write(self.p.root, "spec/checkout_flow_spec.rb", "describe 'checkout' do\n  OrderService.new\nend\n")
        self.configure(match_symbol=False)
        r = self.p.py("scripts/related_tests.py", "app/services/order_service.rb")
        self.assertNotIn("spec/checkout_flow_spec.rb", r.stdout.split())
        self.configure(match_symbol=True)
        r = self.p.py("scripts/related_tests.py", "app/services/order_service.rb")
        self.assertIn("spec/checkout_flow_spec.rb", r.stdout.split())

    def test_match_symbol_ignores_a_bare_word_and_comments(self) -> None:
        self.configure(match_symbol=True)
        write(self.p.root, "app/models/order.rb", "class Order\nend\n")
        write(self.p.root, "spec/cart_spec.rb", "# an order is placed\nit 'keeps the order of items' do\nend\n")
        write(self.p.root, "spec/billing_spec.rb", "# uses Order\nit 'bills' do\n  Order.new\nend\n")
        found = self.p.py("scripts/related_tests.py", "app/models/order.rb").stdout.split()
        self.assertNotIn("spec/cart_spec.rb", found)
        self.assertIn("spec/billing_spec.rb", found)

    def test_junit_reports_by_glob_and_a_broken_report_is_skipped(self) -> None:
        write(self.p.root, "reports/a.xml", '<testsuite><testcase classname="a" name="slow" time="9.5"/></testsuite>')
        write(self.p.root, "reports/b.xml", "<testsuite><testcase")
        self.configure(junit_xml="reports/*.xml")
        r = self.p.py("scripts/related_tests.py", "src/features/orders/order_service.py", "--run")
        self.assertIn("9.50 s a.slow", r.stdout, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_namespaced_import_with_backslashes_is_an_importer(self) -> None:
        self.configure()
        write(self.p.root, "app/Services/OrderService.php", "<?php\nclass OrderService {}\n")
        write(self.p.root, "tests/Feature/CheckoutTest.php", "<?php\nuse App\\Services\\OrderService;\n")
        r = self.p.py("scripts/related_tests.py", "app/Services/OrderService.php")
        self.assertIn("tests/Feature/CheckoutTest.php", r.stdout.split())

    def test_run_reports_its_time_against_the_budget_and_the_slowest_tests(self) -> None:
        write(self.p.root, "report.xml", '<testsuite><testcase classname="a" name="slow" time="9.5"/>'
                                         '<testcase classname="a" name="fast" time="0.1"/></testsuite>')
        self.configure(related_budget_seconds=0, junit_xml="report.xml")
        r = self.p.py("scripts/related_tests.py", "src/features/orders/order_service.py", "--run")
        self.assertIn("over the budget of 0 s", r.stdout)
        self.assertIn("9.50 s a.slow", r.stdout)

    def test_a_changed_snapshot_is_flagged(self) -> None:
        write(self.p.root, "src/features/orders/tests/__snapshots__/test_order_service.snap", "x\n")
        r = self.p.py("scripts/related_tests.py", "src/features/orders/tests/__snapshots__/test_order_service.snap")
        self.assertIn("snapshot changed", r.stdout)

    def test_a_changed_test_is_its_own_related_test(self) -> None:
        r = self.p.py("scripts/related_tests.py", "src/features/billing/tests/test_invoice.py")
        self.assertEqual(r.stdout.split(), ["src/features/billing/tests/test_invoice.py"])

    def test_run_prints_only_failures_and_the_summary(self) -> None:
        r = self.p.py("scripts/related_tests.py", "src/features/orders/order_service.py", "--run")
        lines = r.stdout.splitlines()
        self.assertIn("FAILED fake::test_a", lines)
        self.assertIn("1 failed", lines)
        self.assertTrue((self.p.root / ".claude/prd-flow/state/_tests/related.log").exists())


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

    def test_a_known_flaky_failure_is_reported_but_not_new(self) -> None:
        p = Project()
        try:
            config_path = p.root / "ai-kit.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["tests"]["flaky"] = ["b::three"]
            config_path.write_text(json.dumps(config), encoding="utf-8")
            write(p.root, "baseline.txt", "")
            write(p.root, "final.log", "FAILED b::three\n1 failed\n")
            r = p.py("scripts/new_failures.py", "baseline.txt", "final.log")
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("FLAKY b::three", r.stdout)
            self.assertNotIn("NEW", r.stdout)
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

    def test_setup_runs_the_setup_command(self) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["commands"]["setup"] = "echo setup-ran"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        r = run(self.p.root, BASH, "scripts/gates.sh", "setup")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("setup-ran", r.stdout)

    def test_setup_without_a_configured_command_says_so(self) -> None:
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["commands"].pop("setup", None)
        config_path.write_text(json.dumps(config), encoding="utf-8")
        r = run(self.p.root, BASH, "scripts/gates.sh", "setup")
        self.assertEqual(r.returncode, 2)
        self.assertIn("commands.setup is not set", r.stderr)

    def project_override(self, targets: list[str] | None = None) -> None:
        write(self.p.root, "scripts/gates.project.sh", 'echo "project:$*"\n')
        if targets is not None:
            config_path = self.p.root / "ai-kit.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["commands"]["project_targets"] = targets
            config_path.write_text(json.dumps(config), encoding="utf-8")

    def test_a_target_the_kit_lacks_goes_to_the_project_script(self) -> None:
        self.project_override()
        r = run(self.p.root, BASH, "scripts/gates.sh", "divergence", "--strict")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("project:divergence --strict", r.stdout)

    def test_a_listed_target_goes_to_the_project_script_even_when_the_kit_has_it(self) -> None:
        self.project_override(["setup"])
        r = run(self.p.root, BASH, "scripts/gates.sh", "setup", "x")
        self.assertIn("project:setup x", r.stdout)

    def test_an_unlisted_kit_target_still_runs_the_kit(self) -> None:
        self.project_override(["offline"])
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["commands"]["setup"] = "echo setup-ran"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        r = run(self.p.root, BASH, "scripts/gates.sh", "setup")
        self.assertIn("setup-ran", r.stdout)
        self.assertNotIn("project:", r.stdout)

    def test_an_unknown_target_prints_usage(self) -> None:
        r = run(self.p.root, BASH, "scripts/gates.sh", "nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)


class InvariantGapRatchetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.inv = self.p.root / "docs/trd/invariants.md"
        self.inv.write_text("| ID | Rule | Proof |\n|---|---|---|\n| I-01 | A | gate |\n| I-02 | B | gap |\n| I-03 | C | gap: no test |\n",
                            encoding="utf-8", newline="\n")

    def tearDown(self) -> None:
        self.p.close()

    def allow(self, n) -> None:
        path = self.p.root / "ai-kit.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["allowlist"].pop("invariant_gaps", None)
        if n is not None:
            config["allowlist"]["invariant_gaps"] = n
        path.write_text(json.dumps(config), encoding="utf-8")

    def test_gaps_above_the_entry_fail(self) -> None:
        self.allow(1)
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("invariant_gaps: 2 gap rows, above its allowlist entry 1", r.stdout)

    def test_gaps_below_the_entry_ask_to_lower_it(self) -> None:
        self.allow(3)
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("lower the entry from 3", r.stdout)

    def test_gaps_equal_to_the_entry_pass(self) -> None:
        self.allow(2)
        self.assertEqual(self.p.py("scripts/ratchet.py").returncode, 0)

    def test_escaped_pipes_and_the_word_gap_in_other_forms_do_not_count(self) -> None:
        rows = ["| I-01 | a \\| gap | gate |", "| I-02 | B | no gap here |", "| I-03 | C | gaps closed |", "| I-04 | D | gap |"]
        self.inv.write_text("| ID | Rule | Proof |\n|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        self.allow(1)
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_absent_key_or_file_is_no_error(self) -> None:
        self.allow(None)
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.inv.unlink()
        self.assertEqual(self.p.py("scripts/ratchet.py").returncode, 0)


class CommitTrailersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.base = run(self.p.root, "git", "rev-parse", "HEAD", check=True).stdout.strip()

    def tearDown(self) -> None:
        self.p.close()

    def commit(self, path: str, message: str) -> None:
        write(self.p.root, path, f"x = {len(message)}\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", message, check=True)

    def check(self) -> subprocess.CompletedProcess:
        return self.p.py("scripts/commit_trailers.py", f"{self.base}..HEAD")

    def test_a_source_commit_without_a_trailer_fails(self) -> None:
        self.commit("src/features/orders/more.py", "feat: more")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("feat: more", r.stdout)

    def test_rules_and_case_none_trailers_pass(self) -> None:
        self.commit("src/features/orders/a.py", "feat: a\n\nRules: ORD-01, ORD-02")
        self.commit("src/features/orders/b.py", "fix: b\n\nCase: none (typo in a log line)")
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_case_none_reason_over_eight_words_fails(self) -> None:
        self.commit("src/features/orders/c.py", "fix: c\n\nCase: none (one two three four five six seven eight nine)")
        self.assertEqual(self.check().returncode, 1)

    def test_a_commit_outside_the_source_folders_needs_no_trailer(self) -> None:
        self.commit("docs/notes.md", "docs: notes")
        self.assertEqual(self.check().returncode, 0)

    def test_a_bad_range_prints_the_git_error_and_exits_2(self) -> None:
        r = self.p.py("scripts/commit_trailers.py", "nope..HEAD")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("nope", r.stderr)

    def test_a_path_with_a_space_and_non_ascii_letters_is_seen(self) -> None:
        self.commit("src/features/orders/my café.py", "feat: spaced")
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("feat: spaced", r.stdout)

    @unittest.skipUnless(BASH, "bash not available")
    def test_gates_trailers_runs_the_check_on_a_range(self) -> None:
        self.commit("src/features/orders/d.py", "feat: d")
        r = run(self.p.root, BASH, "scripts/gates.sh", "trailers", f"{self.base}..HEAD")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


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


class KitIdsTest(unittest.TestCase):
    def test_no_contract_id_ships_in_the_kit_or_the_installer(self) -> None:
        import re

        root = KIT.parent
        pattern = re.compile(r"\bK-\d\d\b")
        hits = []
        for folder in (root / "kit", root / "installer"):
            for f in folder.rglob("*") if folder.is_dir() else []:
                if f.is_file() and ".git" not in f.parts and "__pycache__" not in f.parts:
                    text = f.read_bytes().decode("utf-8", errors="ignore")
                    hits += [f"{f.relative_to(root).as_posix()}: {m.group(0)}" for m in pattern.finditer(text)]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()

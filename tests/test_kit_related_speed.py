"""W1.2 to W1.5: the related-tests finder is precise, capped, chunked, extensible and cached."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_kit_scripts import KIT, PY, Project, write


class RelatedSpeedBase(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def configure(self, **tests) -> None:
        path = self.p.root / "ai-kit.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["tests"].update(tests)
        path.write_text(json.dumps(config), encoding="utf-8")

    def related(self, *args: str):
        return self.p.py("scripts/related_tests.py", *args)


class ImportPrecisionTest(RelatedSpeedBase):
    def test_a_stem_that_is_also_a_package_name_does_not_match_every_import(self) -> None:
        write(self.p.root, "src/features/pipeline/stages.py", "x = 1\n")
        write(self.p.root, "src/features/stages/__init__.py", "")
        write(self.p.root, "src/features/stages/runner.py", "x = 1\n")
        write(self.p.root, "src/features/stages/tests/test_runner.py", "from features.stages.runner import x\n")
        r = self.related("src/features/pipeline/stages.py")
        self.assertNotIn("src/features/stages/tests/test_runner.py", r.stdout.split())

    def test_the_full_dotted_path_matches(self) -> None:
        write(self.p.root, "src/features/pipeline/stages.py", "x = 1\n")
        write(self.p.root, "src/features/pipeline/tests/test_flow.py", "from features.pipeline.stages import x\n")
        r = self.related("src/features/pipeline/stages.py")
        self.assertIn("src/features/pipeline/tests/test_flow.py", r.stdout.split())

    def test_a_from_package_import_module_matches(self) -> None:
        write(self.p.root, "src/features/pipeline/stages.py", "x = 1\n")
        write(self.p.root, "src/features/pipeline/tests/test_flow.py", "from features.pipeline import stages\n")
        r = self.related("src/features/pipeline/stages.py")
        self.assertIn("src/features/pipeline/tests/test_flow.py", r.stdout.split())

    def test_an_init_module_is_never_matched_by_its_stem(self) -> None:
        r = self.related("src/features/orders/__init__.py")
        self.assertEqual(r.stdout.split(), [])


class CapTest(RelatedSpeedBase):
    def test_over_the_cap_falls_back_to_the_owning_test_folder_with_a_note(self) -> None:
        for i in range(5):
            write(self.p.root, f"src/features/orders/tests/test_extra{i}.py", "from features.orders.order_service import create_order\n")
        self.configure(related_max_files=3)
        r = self.related("src/features/orders/order_service.py")
        self.assertIn("src/features/orders/tests/test_extra4.py", r.stdout.split())
        self.assertNotIn("src/features/billing/tests/test_invoice.py", r.stdout.split())
        self.assertIn("owning test folder", r.stderr + r.stdout)

    def test_under_the_cap_prints_no_note(self) -> None:
        r = self.related("src/features/orders/order_service.py")
        self.assertNotIn("owning test folder", r.stderr + r.stdout)


class TopLevelTestsCapTest(RelatedSpeedBase):
    def test_over_the_cap_with_only_a_top_level_tests_folder_keeps_the_mirrors_with_a_note(self) -> None:
        write(self.p.root, "lib/widget.py", "x = 1\n")
        write(self.p.root, "tests/test_widget.py", "x = 1\n")
        write(self.p.root, "tests/test_architecture.py", "x = 1\n")
        for i in range(5):
            write(self.p.root, f"tests/test_user{i}.py", "from lib.widget import x\n")
        self.configure(related_max_files=3, always=["tests/test_architecture.py"])
        r = self.related("lib/widget.py")
        out = r.stdout.split()
        self.assertIn("tests/test_widget.py", out)
        self.assertIn("tests/test_architecture.py", out)
        self.assertNotIn("tests/test_user0.py", out)
        self.assertIn("over the cap", r.stderr + r.stdout)


class ArgsFileTest(RelatedSpeedBase):
    def test_args_file_lists_the_changed_files_one_per_line(self) -> None:
        listing = self.p.root / "args.txt"
        listing.write_text("src/features/orders/order_service.py\n\n", encoding="utf-8")
        r = self.related("--args-file", str(listing))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.split(), r.stderr)
        self.assertEqual(r.stdout, self.related("src/features/orders/order_service.py").stdout)


class NativeAlwaysTest(RelatedSpeedBase):
    def test_always_files_still_run_when_native_related_is_set(self) -> None:
        write(self.p.root, "tests/test_architecture.py", "x = 1\n")
        (self.p.root / "native.py").write_text("open('native.txt','a').write('n')\nprint('1 passed')\n", encoding="utf-8")
        (self.p.root / "plain.py").write_text(
            "import sys\nopen('plain.txt','a').write(' '.join(sys.argv[1:]))\nprint('1 passed')\n", encoding="utf-8"
        )
        self.configure(
            native_related=f'"{PY}" native.py {{changed}}',
            runner=f'"{PY}" plain.py {{files}}',
            always=["tests/test_architecture.py"],
        )
        r = self.related("src/features/orders/order_service.py", "--run")
        self.assertIn("exit 0", r.stdout, r.stdout + r.stderr)
        self.assertEqual((self.p.root / "native.txt").read_text(encoding="utf-8"), "n")
        self.assertIn("tests/test_architecture.py", (self.p.root / "plain.txt").read_text(encoding="utf-8"))


class DocsOnlyTest(RelatedSpeedBase):
    def test_a_docs_only_change_runs_nothing_and_caches_nothing(self) -> None:
        (self.p.root / "native.py").write_text("open('native.txt','a').write('n')\nprint('1 passed')\n", encoding="utf-8")
        self.configure(native_related=f'"{PY}" native.py {{changed}}')
        write(self.p.root, "README.md", "# x\n")
        r = self.related("README.md", "--run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("no related tests", r.stdout)
        self.assertFalse((self.p.root / "native.txt").exists())
        self.assertEqual(list(self.p.root.glob("**/related.cache*.json")), [])


class NativeFilterTest(RelatedSpeedBase):
    def test_native_related_gets_only_code_extension_paths(self) -> None:
        (self.p.root / "native.py").write_text(
            "import sys\nopen('native.txt','w').write(' '.join(sys.argv[1:]))\nprint('1 passed')\n", encoding="utf-8"
        )
        self.configure(native_related=f'"{PY}" native.py {{changed}}')
        write(self.p.root, "README.md", "# x\n")
        listing = self.p.root / "args.txt"
        listing.write_text("README.md\nsrc/features/orders/order_service.py\n", encoding="utf-8")
        r = self.related("--args-file", str(listing), "--run")
        self.assertIn("exit 0", r.stdout, r.stdout + r.stderr)
        self.assertEqual((self.p.root / "native.txt").read_text(encoding="utf-8"), "src/features/orders/order_service.py")


class ExcludeTest(RelatedSpeedBase):
    def test_related_exclude_drops_integration_tests(self) -> None:
        write(self.p.root, "tests/integration/test_orders_db.py", "from features.orders.order_service import create_order\n")
        self.assertIn("tests/integration/test_orders_db.py", self.related("src/features/orders/order_service.py").stdout.split())
        self.configure(related_exclude=["tests/integration/**"])
        out = self.related("src/features/orders/order_service.py").stdout.split()
        self.assertNotIn("tests/integration/test_orders_db.py", out)
        self.assertIn("src/features/orders/tests/test_order_service.py", out)

    def test_related_exclude_also_drops_always_entries(self) -> None:
        write(self.p.root, "tests/integration/test_arch.py", "x = 1\n")
        self.configure(always=["tests/integration/test_arch.py"], related_exclude=["tests/integration/**"])
        self.assertNotIn("tests/integration/test_arch.py", self.related("src/features/orders/order_service.py").stdout.split())

    def test_the_default_config_excludes_nothing(self) -> None:
        config = json.loads((KIT / "ai-kit.json").read_text(encoding="utf-8"))
        self.assertEqual(config["tests"]["related_exclude"], [])


class BudgetTest(RelatedSpeedBase):
    def test_always_entries_do_not_count_toward_the_budget(self) -> None:
        write(self.p.root, "tests/test_architecture.py", "x = 1\n")
        (self.p.root / "slow.py").write_text(
            "import sys,time\nif any('test_architecture' in a for a in sys.argv):\n    time.sleep(2)\nprint('1 passed')\n", encoding="utf-8"
        )
        self.configure(runner=f'"{PY}" slow.py {{files}}', always=["tests/test_architecture.py"], related_budget_seconds=1)
        r = self.related("src/features/orders/order_service.py", "--run")
        self.assertIn("exit 0", r.stdout, r.stdout + r.stderr)
        self.assertNotIn("over the budget", r.stdout)

    def test_a_slow_selected_test_still_trips_the_budget(self) -> None:
        (self.p.root / "slow.py").write_text("import time\ntime.sleep(2)\nprint('1 passed')\n", encoding="utf-8")
        self.configure(runner=f'"{PY}" slow.py {{files}}', related_budget_seconds=1)
        r = self.related("src/features/orders/order_service.py", "--run")
        self.assertIn("over the budget", r.stdout)


class LogPerSlugTest(RelatedSpeedBase):
    def run_with_context(self, slug: str | None):
        import os
        import subprocess

        env = {k: v for k, v in os.environ.items() if k != "AI_KIT_CONTEXT"}
        if slug:
            env["AI_KIT_CONTEXT"] = slug
        self.configure(runner=f'"{PY}" -c "print(\'1 passed\')" {{files}}')
        return subprocess.run([PY, "scripts/related_tests.py", "src/features/orders/order_service.py", "--run"],
                              cwd=self.p.root, capture_output=True, text=True, encoding="utf-8", env=env, check=False)

    def test_the_log_and_cache_carry_the_slug(self) -> None:
        r = self.run_with_context("slug-a")
        self.assertIn("related-slug-a.log", r.stdout)
        log_dir = self.p.root / json.loads((self.p.root / "ai-kit.json").read_text(encoding="utf-8"))["tests"]["log_dir"]
        self.assertTrue((log_dir / "related-slug-a.log").is_file())
        self.assertFalse((log_dir / "related.log").exists())

    def test_without_a_context_the_shared_name_stays(self) -> None:
        self.assertIn("related.log", self.run_with_context(None).stdout)


class ConfigManyKeysTest(RelatedSpeedBase):
    def test_many_keys_resolve_in_one_call(self) -> None:
        r = self.p.py("scripts/config_get.py", "--many", "tests.related_budget_seconds", "tests.nope", "commands.python")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "tests.related_budget_seconds=60")
        self.assertEqual(lines[1], "tests.nope=")
        self.assertEqual(len(lines), 3)


class ListedFilesFallbackTest(unittest.TestCase):
    def test_the_fallback_walk_skips_the_git_folder(self) -> None:
        scripts = str(KIT / "scripts")
        sys.path.insert(0, scripts)
        try:
            from kit_config import listed_files

            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                (root / ".git").mkdir()
                (root / ".git" / "config").write_text("x", encoding="utf-8")
                (root / "a.py").write_text("x", encoding="utf-8")
                self.assertEqual(listed_files(root), ["a.py"])
        finally:
            sys.path.remove(scripts)
            sys.modules.pop("kit_config", None)


class AlwaysTest(RelatedSpeedBase):
    def test_tests_always_is_appended(self) -> None:
        write(self.p.root, "tests/test_architecture.py", "x = 1\n")
        self.configure(always=["tests/test_architecture.py"])
        r = self.related("src/features/orders/order_service.py")
        self.assertIn("tests/test_architecture.py", r.stdout.split())


class RunnerTest(RelatedSpeedBase):
    def argv_runner(self) -> None:
        script = self.p.root / "echo_args.py"
        script.write_text(
            "import sys\nopen('calls.txt','a').write(str(len(sys.argv)-1)+'\\n')\nprint('1 passed')\n", encoding="utf-8"
        )
        self.configure(runner=f'"{PY}" echo_args.py {{files}}', related_max_files=10000, related_cmd_chars=300)

    def test_a_long_selection_is_chunked_under_the_command_limit(self) -> None:
        self.argv_runner()
        for i in range(40):
            write(self.p.root, f"src/features/orders/tests/test_long_name_number_{i}.py", "from features.orders.order_service import create_order\n")
        r = self.related("src/features/orders/order_service.py", "--run")
        self.assertIn("exit 0", r.stdout, r.stdout + r.stderr)
        calls = (self.p.root / "calls.txt").read_text(encoding="utf-8").split()
        self.assertGreater(len(calls), 1)
        self.assertEqual(sum(int(c) for c in calls), 41)

    def test_shell_metacharacters_in_a_name_are_not_interpreted(self) -> None:
        self.argv_runner()
        write(self.p.root, "src/features/orders/tests/test_a&b.py", "from features.orders.order_service import create_order\n")
        r = self.related("src/features/orders/order_service.py", "--run")
        self.assertIn("exit 0", r.stdout, r.stdout + r.stderr)


class CacheTest(RelatedSpeedBase):
    def test_an_identical_rerun_is_skipped_and_a_changed_file_runs_again(self) -> None:
        script = self.p.root / "count.py"
        script.write_text("open('runs.txt','a').write('x')\nprint('1 passed')\n", encoding="utf-8")
        self.configure(runner=f'"{PY}" count.py {{files}}')
        target = "src/features/orders/order_service.py"
        self.related(target, "--run")
        r = self.related(target, "--run")
        self.assertIn("unchanged since the last run", r.stdout)
        self.assertEqual((self.p.root / "runs.txt").read_text(encoding="utf-8"), "x")
        write(self.p.root, target, "x = 99\n")
        self.related(target, "--run")
        self.assertEqual((self.p.root / "runs.txt").read_text(encoding="utf-8"), "xx")

    def test_a_failed_run_is_never_served_from_the_cache(self) -> None:
        r1 = self.related("src/features/orders/order_service.py", "--run")
        r2 = self.related("src/features/orders/order_service.py", "--run")
        self.assertNotIn("unchanged since the last run", r2.stdout)
        self.assertIn("1 failed", r2.stdout, r1.stdout)


if __name__ == "__main__":
    unittest.main()

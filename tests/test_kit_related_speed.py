"""W1.2 to W1.5: the related-tests finder is precise, capped, chunked, extensible and cached."""

import json
import unittest

from tests.test_kit_scripts import PY, Project, write


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

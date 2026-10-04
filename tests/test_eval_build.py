"""EV04: eval/build.py builds a fresh project for each arm that passes its own gates."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "eval" / "build.py"
PY = sys.executable


def load_build():
    spec = importlib.util.spec_from_file_location("eval_build", BUILD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False)


class BuildChecks:
    ref = ""
    spec_kit = False

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "project"
        args = [PY, str(BUILD), "--ref", cls.ref, "--out", str(cls.out)]
        if cls.spec_kit:
            args.append("--spec-kit")
        cls.built = run(args, ROOT)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_succeeds(self):
        self.assertEqual(self.built.returncode, 0, self.built.stdout + self.built.stderr)

    def test_no_placeholder_left_outside_templates(self):
        self.assertEqual(load_build().find_leftovers(self.out), [])

    def test_gate_passes(self):
        result = run([PY, ".claude/skills/prd-gate/scripts/gate.py"], self.out)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_visible_suite_passes(self):
        result = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"], self.out)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_one_seed_commit(self):
        log = run(["git", "log", "--format=%s"], self.out).stdout.split("\n")
        self.assertEqual([line for line in log if line], ["chore: seed"])

    def test_tree_is_clean_after_the_checks(self):
        self.assertEqual(run(["git", "status", "--porcelain"], self.out).stdout.strip(), "")


class LivingTruthArm(BuildChecks, unittest.TestCase):
    ref = "feat/living-truth"

    def test_no_spec_kit_files(self):
        self.assertFalse((self.out / ".claude" / "commands").exists())
        self.assertFalse((self.out / ".specify" / "templates").exists())


class CurrentFlowWithoutSpecKit(BuildChecks, unittest.TestCase):
    ref = "main"


@unittest.skipUnless(os.environ.get("EVAL_SPEC_KIT") == "1", "set EVAL_SPEC_KIT=1 to run the spec-kit path (network)")
class CurrentFlowWithSpecKit(BuildChecks, unittest.TestCase):
    ref = "main"
    spec_kit = True

    def test_spec_kit_files_are_present(self):
        self.assertTrue((self.out / ".specify" / "templates").exists())

    def test_constitution_is_the_kits(self):
        text = (self.out / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
        self.assertIn("# Orders Constitution", text)


if __name__ == "__main__":
    unittest.main()

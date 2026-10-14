"""docs-flow-eval ships in the kit (plan-rule-as-data S11, E1 to E4).

The kit carries the skill and its two agents; worktrees.py setup --kit overlays the kit's
prd-flow files on the scenario base as one seed commit; the arm names the dedicated executor;
quality.py uses the overlaid kit's gate and index generator.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "kit" / ".claude" / "skills" / "docs-flow-eval"
AGENTS = ROOT / "kit" / ".claude" / "agents"
WORKTREES = SKILL / "scripts" / "worktrees.py"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class KitShipsEvalTest(unittest.TestCase):
    def test_skill_and_agents_live_in_the_kit(self):
        for rel in ("SKILL.md", "arms/current-prd-flow.md", "scripts/worktrees.py", "scripts/quality.py",
                    "scripts/metrics.py", "scenarios/README.md"):
            self.assertTrue((SKILL / rel).is_file(), rel)
        for name in ("docs-eval-executor.md", "docs-eval-reader.md"):
            self.assertTrue((AGENTS / name).is_file(), name)

    def test_one_copy_of_every_script(self):
        own = ROOT / ".claude" / "skills" / "docs-flow-eval"
        self.assertFalse((own / "scripts").exists())
        self.assertFalse((own / "SKILL.md").exists())
        self.assertTrue((own / "scenarios" / "reconnect-window-90" / "scenario.json").is_file())
        self.assertFalse((ROOT / ".claude" / "agents" / "docs-eval-executor.md").exists())

    def test_skill_md_stays_under_the_ratchet_limit(self):
        limit = json.loads((ROOT / "kit" / "ai-kit.json").read_text(encoding="utf-8"))["limits"]["skill_md_bytes"]
        self.assertLessEqual((SKILL / "SKILL.md").stat().st_size, limit)

    def test_private_gate_and_index_are_gone(self):
        self.assertFalse(list(SKILL.rglob("gate_lite.py")))
        self.assertFalse(list(SKILL.rglob("gen_index.py")))
        self.assertFalse(list((ROOT / ".claude" / "skills" / "docs-flow-eval").rglob("gate_lite.py")))

    def test_arm_uses_the_dedicated_executor_and_no_workaround(self):
        arm = (SKILL / "arms" / "current-prd-flow.md").read_text(encoding="utf-8")
        self.assertIn("docs-eval-executor", arm)
        self.assertIn("never `general-purpose`", arm)
        self.assertNotIn("NO_COLOR", arm)
        self.assertNotIn("TEMP", arm)

    def test_quality_uses_the_kit_gate(self):
        text = (SKILL / "scripts" / "quality.py").read_text(encoding="utf-8")
        self.assertIn(".claude/skills/prd-flow/scripts/gate.py", text)
        self.assertIn(".claude/skills/prd-flow/scripts/gen_index.py", text)
        self.assertNotIn("gate_lite", text)
        self.assertNotIn("HERE /", text)


class SetupKitOverlayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "scenario-repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        write(self.repo / "docs" / "prd.md", "old\n")
        write(self.repo / ".claude" / "skills" / "prd-flow" / "repo.md", "scenario repo.md\n")
        write(self.repo / ".claude" / "skills" / "prd-flow" / "SKILL.md", "old skill\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")

        self.kit = self.tmp / "kit-repo"
        flow = self.kit / "kit" / ".claude" / "skills" / "prd-flow"
        write(flow / "SKILL.md", "new skill\n")
        write(flow / "repo.md", "kit repo.md must not overlay\n")
        write(flow / "scripts" / "gate.py", "print('gate')\n")
        write(self.kit / "kit" / ".claude" / "agents" / "prd-flow-executor.md", "executor\n")
        write(self.kit / "kit" / "scripts" / "gates.sh", "echo gates\n")
        write(self.kit / "kit" / "docs" / "templates" / "prd-section.md", "template\n")

        fixtures = self.tmp / "sc" / "fixtures"
        write(fixtures / "sheet.md", "sheet {WORKTREE}\n")
        self.scenario = self.tmp / "sc" / "scenario.json"
        write(self.scenario, json.dumps({"name": "fake", "repo": self.repo.as_posix(), "base": self.base,
                                         "slug": "fake-slug", "fixtures": "fixtures/"}))
        self.env = {**os.environ, "DOCS_EVAL_ROOT": (self.tmp / "evalroot").as_posix()}

    def tearDown(self):
        import shutil
        subprocess.run(["git", "-C", str(self.repo), "worktree", "prune"], capture_output=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_wt(self, *args):
        return subprocess.run(["python", str(WORKTREES), *args], env=self.env, capture_output=True, text=True)

    def test_setup_kit_makes_one_seed_commit_and_teardown_removes(self):
        r = self.run_wt("setup", str(self.scenario), "run1", "--kit", str(self.kit))
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = self.tmp / "evalroot" / "fake" / "run1"
        self.assertEqual(git(wt, "rev-list", "--count", f"{self.base}..HEAD"), "1")
        changed = set(git(wt, "diff", "--name-only", self.base, "HEAD").splitlines())
        self.assertEqual(changed, {
            ".claude/skills/prd-flow/SKILL.md",
            ".claude/skills/prd-flow/scripts/gate.py",
            ".claude/agents/prd-flow-executor.md",
            "scripts/gates.sh",
            "docs/templates/prd-section.md",
        })
        self.assertEqual((wt / ".claude/skills/prd-flow/repo.md").read_text(encoding="utf-8"), "scenario repo.md\n")
        self.assertEqual(git(wt, "status", "--short", "--", ".", ":!.claude/prd-flow"), "")
        sheet = wt / ".claude/prd-flow/state/fake-slug/sheet.md"
        self.assertIn(wt.as_posix(), sheet.read_text(encoding="utf-8"))
        t = self.run_wt("teardown", str(self.scenario), "run1")
        self.assertEqual(t.returncode, 0, t.stderr)
        self.assertFalse(wt.exists())

    def test_setup_without_kit_adds_no_commit(self):
        r = self.run_wt("setup", str(self.scenario), "run2")
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = self.tmp / "evalroot" / "fake" / "run2"
        self.assertEqual(git(wt, "rev-list", "--count", f"{self.base}..HEAD"), "0")
        self.run_wt("teardown", str(self.scenario), "run2")


if __name__ == "__main__":
    unittest.main()

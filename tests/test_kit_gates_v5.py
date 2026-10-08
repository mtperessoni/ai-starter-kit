"""Base resolver, gate result lines, gates.sh close and html, and the SKILL.md size ratchet."""

import json
import re
import os
import shutil
import subprocess
import sys
import unittest

from tests.test_kit_scripts import BASH, KIT, PY, Project, run, write


class ResolveBaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        sys.path.insert(0, str(self.p.root / "scripts"))
        import kit_config

        self.kc = kit_config

    def tearDown(self) -> None:
        sys.path.remove(str(self.p.root / "scripts"))
        sys.modules.pop("kit_config", None)
        self.p.close()

    def test_the_local_base_branch_is_used_without_origin(self) -> None:
        self.assertEqual(self.kc.resolve_base(self.p.root), "main")

    def test_origin_wins_when_it_exists(self) -> None:
        run(self.p.root, "git", "update-ref", "refs/remotes/origin/main", "HEAD", check=True)
        self.assertEqual(self.kc.resolve_base(self.p.root), "origin/main")

    def test_a_missing_base_branch_says_pass_base(self) -> None:
        run(self.p.root, "git", "branch", "-m", "trunk", check=True)
        with self.assertRaises(self.kc.BaseError) as ctx:
            self.kc.resolve_base(self.p.root)
        self.assertIn("pass --base", str(ctx.exception))

    def test_an_explicit_missing_ref_is_an_error_never_green(self) -> None:
        with self.assertRaises(self.kc.BaseError) as ctx:
            self.kc.resolve_base(self.p.root, "nope")
        self.assertIn("nope", str(ctx.exception))
        self.assertEqual(self.kc.resolve_base(self.p.root, "HEAD"), "HEAD")

    def test_trailers_default_to_the_resolved_base(self) -> None:
        run(self.p.root, "git", "checkout", "-q", "-b", "feat", check=True)
        write(self.p.root, "src/features/orders/more.py", "x = 1\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "feat: more", check=True)
        r = self.p.py("scripts/commit_trailers.py")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("feat: more", r.stdout)

    def test_trailers_with_a_missing_base_exit_2(self) -> None:
        r = self.p.py("scripts/commit_trailers.py", "--base", "nope")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("nope", r.stderr)

    def test_related_with_a_missing_base_is_an_error(self) -> None:
        r = self.p.py("scripts/related_tests.py", "--base", "nope")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("nope", r.stderr)

    def test_related_defaults_to_the_local_base_branch(self) -> None:
        write(self.p.root, "src/features/orders/order_service.py", '"""ORD-01."""\nx = 2\n')
        r = self.p.py("scripts/related_tests.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("order_service.py", r.stdout)


@unittest.skipUnless(BASH, "bash not available")
class GatesV5Test(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def configure(self, **commands: str) -> None:
        path = self.p.root / "ai-kit.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["commands"].update(commands)
        path.write_text(json.dumps(config), encoding="utf-8")

    def gates(self, *args: str) -> subprocess.CompletedProcess:
        return run(self.p.root, BASH, "scripts/gates.sh", *args)

    def test_lint_prints_one_ok_line(self) -> None:
        self.configure(lint=f'"{PY}" -c "pass"')
        r = self.gates("lint")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("lint ok", r.stdout)

    def test_a_failing_lint_prints_the_exit_and_the_log(self) -> None:
        self.configure(lint=f'"{PY}" -c "import sys; print(\'bad style\'); sys.exit(3)"')
        r = self.gates("lint")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("lint FAILED (exit 3), log .claude/prd-flow/state/_tests/lint.log", r.stdout)
        log = (self.p.root / ".claude/prd-flow/state/_tests/lint.log").read_text(encoding="utf-8")
        self.assertIn("bad style", log)

    def test_fix_and_imports_print_their_result_lines(self) -> None:
        self.configure(fix=f'"{PY}" -c "pass"', import_check=f'"{PY}" -c "raise SystemExit(1)"')
        self.assertIn("fix ok", self.gates("fix").stdout)
        self.assertIn("imports FAILED (exit 1), log ", self.gates("imports").stdout)

    def test_html_runs_the_skill_builder_by_its_real_path(self) -> None:
        shutil.copytree(KIT / "docs" / "templates", self.p.root / "docs" / "templates", dirs_exist_ok=True)
        r = self.gates("html")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("wrote", r.stdout)
        r = self.gates("html", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_usage_lists_close_and_html(self) -> None:
        r = self.gates("nope")
        self.assertIn("close [slug]", r.stderr)
        self.assertIn("html", r.stderr)

    def close_setup(self, lint: str = "pass") -> None:
        self.configure(test=f'"{PY}" -c "print(\'1 passed\')"', offline_args="", lint=f'"{PY}" -c "{lint}"')
        shutil.copytree(KIT / "docs" / "templates", self.p.root / "docs" / "templates", dirs_exist_ok=True)
        self.gates("html")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "html", check=True)
        self.gates("baseline", "demo")

    def test_close_prints_one_short_block_and_logs_the_rest(self) -> None:
        self.close_setup()
        r = self.gates("close", "demo")
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 15, r.stdout)
        self.assertIn("lint ok", r.stdout)

    def test_close_on_success_clears_the_slug_state_and_its_log(self) -> None:
        self.close_setup()
        state = self.p.root / ".claude/prd-flow/state"
        write(self.p.root, ".claude/prd-flow/state/_gate/last.txt", "x")
        r = self.gates("close", "demo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((state / "demo").exists())
        self.assertFalse((state / "_gate").exists())
        self.assertFalse((state / "_close/demo.log").exists())

    def test_close_on_failure_deletes_nothing_and_keeps_the_log(self) -> None:
        self.close_setup(lint="import sys; sys.exit(1)")
        state = self.p.root / ".claude/prd-flow/state"
        self.gates("close", "demo")
        self.assertTrue((state / "demo/baseline-failures.txt").is_file())
        self.assertTrue((state / "_close/demo.log").is_file())

    def test_close_rejects_a_slug_with_a_path_separator_or_dotdot(self) -> None:
        for bad in ("../x", "a/b", "a..b"):
            r = run(self.p.root, PY, "scripts/close_gate.py", bad)
            self.assertNotEqual(r.returncode, 0, bad)
            self.assertIn("separator", r.stdout)

    def test_close_turns_a_missing_bash_into_a_failed_line(self) -> None:
        self.close_setup()
        env_run = subprocess.run([PY, "scripts/close_gate.py", "demo"], cwd=self.p.root, capture_output=True, text=True,
                                 encoding="utf-8", env={**os.environ, "GATES_BASH": str(self.p.root / "no-such-bash")}, check=False)
        self.assertEqual(env_run.returncode, 1, env_run.stdout + env_run.stderr)
        self.assertIn("FAILED", env_run.stdout)
        self.assertNotIn("Traceback", env_run.stderr)

    def test_close_fails_when_a_step_fails(self) -> None:
        self.close_setup(lint="import sys; sys.exit(1)")
        r = self.gates("close", "demo")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("lint FAILED", r.stdout)
        self.assertIn("owner: executor fix", r.stdout)
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 15)

    def test_close_without_a_baseline_says_so(self) -> None:
        self.configure(test=f'"{PY}" -c "print(1)"', offline_args="", lint=f'"{PY}" -c "pass"')
        r = self.gates("close", "nobase")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("baseline missing: run scripts/gates.sh baseline nobase before the first task", r.stdout)
        self.assertIn("owner: user", r.stdout)
        self.assertNotIn("owner: executor fix", r.stdout)
        self.assertIn("next: user chooses", r.stdout)

    def stub_gates(self, lint_out: str = "", lint_rc: int = 0, trailers_out: str = "", trailers_rc: int = 0) -> None:
        write(self.p.root, "scripts/gates.sh", f"""case "$1" in
lint) printf '%b' '{lint_out}'; exit {lint_rc} ;;
trailers) printf '%b' '{trailers_out}'; exit {trailers_rc} ;;
retro) echo "retro demo: 7 finding(s), wall 10 s, wait 0 s"
  echo "  F1 [medium] value 3, threshold 2, seq [1]"
  echo "  F2 [high] value 9, threshold 2, seq [2]"
  echo "  F3 [low] value 3, threshold 2, seq [3]"
  echo "  F4 [medium] value 3, threshold 2, seq [4]"
  echo "  F5 [high] value 8, threshold 2, seq [5]"
  echo "  F6 [medium] value 3, threshold 2, seq [6]"
  echo "  F7 [critical] value 30, threshold 2, seq [7]"
  echo "  report: .ai-kit/runs/demo/retro.md" ;;
*) echo "$1 ok" ;;
esac
""")
        write(self.p.root, ".claude/prd-flow/state/demo/baseline-failures.txt", "")

    def close_direct(self):
        env = {**os.environ, "GATES_BASH": BASH}
        return subprocess.run([PY, "scripts/close_gate.py", "demo"], cwd=self.p.root, capture_output=True, text=True,
                              encoding="utf-8", env=env, check=False)

    def test_close_prints_at_most_five_retro_findings_highest_severity_first(self) -> None:
        self.stub_gates()
        r = self.close_direct()
        lines = r.stdout.splitlines()
        found = [ln for ln in lines if re.match(r"\s+F\d \[", ln)]
        self.assertEqual(len(found), 5, r.stdout)
        self.assertIn("F7 [critical]", found[0])
        self.assertIn("[high]", found[1])
        self.assertNotIn("F3", r.stdout)
        self.assertIn("retro demo: 7 finding(s)", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_failing_close_prints_the_last_ten_error_lines_of_the_failed_check(self) -> None:
        out = "\n".join(f"error line {i}" for i in range(1, 21)) + "\n"
        self.stub_gates(lint_out=out, lint_rc=1)
        r = self.close_direct()
        self.assertEqual(r.returncode, 1, r.stdout)
        shown = [ln for ln in r.stdout.splitlines() if "error line" in ln]
        self.assertEqual(len(shown), 10, r.stdout)
        self.assertIn("error line 20", shown[-1])
        self.assertNotIn("error line 10", r.stdout)

    def test_a_failure_prints_a_next_line_naming_the_dispatch(self) -> None:
        self.stub_gates(lint_out="bad\n", lint_rc=1)
        r = self.close_direct()
        self.assertIn("owner: executor fix", r.stdout)
        self.assertIn("next: executor fix with the printed lines, then executor close", r.stdout)

    def test_a_trailer_on_an_older_commit_needs_a_history_rewrite_and_goes_to_the_user(self) -> None:
        self.stub_gates(trailers_out="deadbeef fix: x: touches the source folders without a trailer\n", trailers_rc=1)
        r = self.close_direct()
        self.assertIn("trailers FAILED", r.stdout)
        self.assertIn("owner: user", r.stdout)
        self.assertIn("next: user chooses", r.stdout)
        self.assertNotIn("owner: executor fix", r.stdout)

    def test_a_trailer_missing_only_on_head_is_an_executor_fix(self) -> None:
        head = subprocess.run(["git", "-C", str(self.p.root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()[:8]
        self.stub_gates(trailers_out=f"{head} fix: x: touches the source folders without a trailer\n", trailers_rc=1)
        r = self.close_direct()
        self.assertIn("owner: executor fix", r.stdout)

    def test_truncation_keeps_the_owner_and_next_lines_when_several_steps_fail(self) -> None:
        out = "\n".join(f"err {i}" for i in range(1, 12)) + "\n"
        self.stub_gates(lint_out=out, lint_rc=1, trailers_out="deadbeef a\n" + out, trailers_rc=1)
        r = self.close_direct()
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 24, r.stdout)
        self.assertEqual(r.stdout.count("owner:"), 2, r.stdout)
        self.assertEqual(r.stdout.count("next:"), 2, r.stdout)


class SkillMdRatchetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        for skill in (self.p.root / ".claude/skills").iterdir():
            if (skill / "SKILL.md").exists():
                (skill / "SKILL.md").write_text("small\n", encoding="utf-8")
        self.skill = write(self.p.root, ".claude/skills/big/SKILL.md", "x" * 7000)

    def tearDown(self) -> None:
        self.p.close()

    def allow(self, entries: dict) -> None:
        path = self.p.root / "ai-kit.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["allowlist"]["skill_md_bytes"] = entries
        path.write_text(json.dumps(config), encoding="utf-8")

    def test_a_skill_over_the_limit_fails_until_allowlisted(self) -> None:
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn(".claude/skills/big/SKILL.md", r.stdout)
        self.allow({".claude/skills/big/SKILL.md": 7000})
        self.assertEqual(self.p.py("scripts/ratchet.py").returncode, 0)

    def test_growing_fails_and_shrinking_asks_to_lower_the_entry(self) -> None:
        self.allow({".claude/skills/big/SKILL.md": 7000})
        self.skill.write_text("x" * 7100, encoding="utf-8")
        self.assertIn("above its allowlist entry", self.p.py("scripts/ratchet.py").stdout)
        self.skill.write_text("x" * 6500, encoding="utf-8")
        self.assertIn("lower the entry", self.p.py("scripts/ratchet.py").stdout)

    def test_a_skill_under_the_limit_with_an_entry_must_drop_it(self) -> None:
        self.skill.write_text("x" * 6000, encoding="utf-8")
        self.allow({".claude/skills/big/SKILL.md": 7000})
        r = self.p.py("scripts/ratchet.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("remove the entry", r.stdout)

    def test_the_limit_comes_from_the_config(self) -> None:
        self.skill.write_text("x" * 6000, encoding="utf-8")
        path = self.p.root / "ai-kit.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["limits"]["skill_md_bytes"] = 5000
        path.write_text(json.dumps(config), encoding="utf-8")
        self.assertEqual(self.p.py("scripts/ratchet.py").returncode, 1)

    def test_the_kit_config_carries_the_limit(self) -> None:
        config = json.loads((KIT / "ai-kit.json").read_text(encoding="utf-8"))
        self.assertEqual(config["limits"]["skill_md_bytes"], 6144)


if __name__ == "__main__":
    unittest.main()

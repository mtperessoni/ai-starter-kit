"""Kit tools: gates.sh fix-files, lint-files, move, settings-check, next_change_number.py, the hook launcher and the installer notes."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_kit_scripts import BASH, KIT, PY, Project, run, write

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "installer" / "ai-kit"


def set_commands(p: Project, **commands: str) -> None:
    path = p.root / "ai-kit.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["commands"].update(commands)
    path.write_text(json.dumps(config), encoding="utf-8")


def echo_to(log: str) -> str:
    return f'"{PY}" -c "import sys; open(r\'{log}\', \'a\').write(\' \'.join(sys.argv[1:]) + chr(10))"'


@unittest.skipUnless(BASH, "bash not available")
class FilesTargetsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.log = self.p.root / "calls.log"

    def tearDown(self) -> None:
        self.p.close()

    def gates(self, *args: str) -> subprocess.CompletedProcess:
        return run(self.p.root, BASH, "scripts/gates.sh", *args)

    def test_fix_files_runs_the_configured_command_on_only_those_files(self) -> None:
        set_commands(self.p, fix_file=echo_to(self.log.as_posix()) + " {files}", fix="exit 9")
        r = self.gates("fix-files", "a.py", "b.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("fix-files ok", r.stdout)
        self.assertEqual(self.log.read_text(encoding="utf-8").split(), ["a.py", "b.py"])

    def test_lint_files_reports_a_failure_with_its_log(self) -> None:
        set_commands(self.p, lint_file=f'"{PY}" -c "import sys; sys.exit(3)" {{files}}')
        r = self.gates("lint-files", "a.py")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("lint-files FAILED (exit 3)", r.stdout)

    def test_many_files_run_in_chunks(self) -> None:
        set_commands(self.p, fix_file=echo_to(self.log.as_posix()) + " {files}")
        names = [f"f{i}.py" for i in range(60)]
        r = self.gates("fix-files", *names)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertGreater(len(calls), 1)
        self.assertEqual(" ".join(calls).split(), names)

    def test_unset_falls_back_to_the_repo_wide_command_with_a_note(self) -> None:
        set_commands(self.p, fix=echo_to(self.log.as_posix()) + " whole")
        r = self.gates("fix-files", "a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("commands.fix_file", r.stderr)
        self.assertEqual(self.log.read_text(encoding="utf-8").split(), ["whole"])

    def test_no_files_is_a_usage_error(self) -> None:
        self.assertEqual(self.gates("lint-files").returncode, 2)

    def test_move_wraps_move_lines_with_its_arguments(self) -> None:
        write(self.p.root, "a.txt", "1\n2\n3\n4\n")
        write(self.p.root, "b.txt", "x\ny\n")
        r = self.gates("move", "a.txt", "2", "3", "b.txt", "--at", "2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.p.root / "a.txt").read_text(encoding="utf-8"), "1\n4\n")
        self.assertEqual((self.p.root / "b.txt").read_text(encoding="utf-8"), "x\n2\n3\ny\n")

    def test_settings_check_target_runs(self) -> None:
        write(self.p.root, ".claude/settings.local.json", json.dumps({"permissions": {"deny": ["Edit(docs/prd/**)"]}}))
        r = self.gates("settings-check")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("docs/prd", r.stdout)


class SettingsCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def deny(self, *rules: str, name: str = "settings.json") -> subprocess.CompletedProcess:
        write(self.p.root, f".claude/{name}", json.dumps({"permissions": {"deny": list(rules)}}))
        return self.p.py("scripts/settings_check.py")

    def test_the_kit_settings_pass(self) -> None:
        r = self.p.py("scripts/settings_check.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_deny_of_a_written_folder_fails(self) -> None:
        for rule in ("Edit(docs/trd/**)", "Write(changes/**)", "Read(docs/prd/CHANGELOG.md)",
                     "Edit(.claude/prd-flow/state/**)", "Write(**/*.md)", "Edit"):
            with self.subTest(rule=rule):
                r = self.deny(rule)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(rule, r.stdout)

    def test_the_local_file_is_read_too(self) -> None:
        r = self.deny("Read(docs/prd/**)", name="settings.local.json")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("settings.local.json", r.stdout)

    def test_unrelated_denies_pass(self) -> None:
        r = self.deny("Read(.env)", "Edit(src/generated/**)", "Bash(rm:*)")
        self.assertEqual(r.returncode, 0, r.stdout)


class NextChangeNumberTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_the_first_number_is_001_and_the_folder_exists(self) -> None:
        r = self.p.py("scripts/next_change_number.py", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "changes/001-alpha")
        self.assertTrue((self.p.root / "changes" / "001-alpha").is_dir())

    def test_the_archive_counts(self) -> None:
        (self.p.root / "changes" / "archive" / "007-old").mkdir(parents=True)
        (self.p.root / "changes" / "003-live").mkdir()
        r = self.p.py("scripts/next_change_number.py", "beta")
        self.assertEqual(r.stdout.strip(), "changes/008-beta")

    def test_a_marker_left_by_a_crash_is_skipped(self) -> None:
        (self.p.root / "changes" / ".reserve-001").mkdir(parents=True)
        r = self.p.py("scripts/next_change_number.py", "gamma")
        self.assertEqual(r.stdout.strip(), "changes/002-gamma")

    def test_parallel_reservations_get_different_numbers(self) -> None:
        procs = [subprocess.Popen([PY, "scripts/next_change_number.py", f"s{i}"], cwd=self.p.root,  # noqa: S603
                                  stdout=subprocess.PIPE, text=True) for i in range(8)]
        outs = [proc.communicate()[0].strip() for proc in procs]
        numbers = [re.match(r"changes/(\d+)-", out).group(1) for out in outs]
        self.assertEqual(len(set(numbers)), 8, outs)
        folders = sorted(d.name for d in (self.p.root / "changes").iterdir())
        self.assertEqual(len(folders), 8, folders)


class HookLauncherTest(unittest.TestCase):
    def commands(self) -> list[str]:
        settings = json.loads((KIT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        return [h["command"] for entries in settings["hooks"].values() for e in entries for h in e["hooks"]]

    def test_every_entry_has_the_same_launcher(self) -> None:
        self.assertEqual(len(set(self.commands())), 1)

    def test_the_configured_python_is_used_without_a_probe(self) -> None:
        command = self.commands()[0]
        self.assertEqual(command.count("-c pass"), 1, "the probe stays only for the fallback")
        self.assertRegex(command, r'\[ -z "\$c" \]')

    def test_launcher_runs_the_hook_with_the_configured_python(self) -> None:
        p = Project()
        try:
            marker = p.root / "ran.txt"
            write(p.root, "scripts/telemetry_hook.py", f"open(r'{marker}', 'w').write('x')\n")
            config = json.loads((p.root / "ai-kit.json").read_text(encoding="utf-8"))
            config["commands"]["python"] = Path(PY).as_posix()
            write(p.root, "ai-kit.json", json.dumps(config))
            if BASH:
                env_cmd = self.commands()[0]
                r = subprocess.run([BASH, "-c", env_cmd], cwd=p.root, env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": p.root.as_posix()},  # noqa: S603
                                   capture_output=True, text=True, check=False)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(marker.exists())
        finally:
            p.close()

    def test_launcher_fails_open_without_any_python(self) -> None:
        if not BASH:
            self.skipTest("bash not available")
        p = Project()
        try:
            config = json.loads((p.root / "ai-kit.json").read_text(encoding="utf-8"))
            config["commands"]["python"] = "no-such-python-xyz"
            write(p.root, "ai-kit.json", json.dumps(config))
            r = subprocess.run([BASH, "-c", self.commands()[0]], cwd=p.root, env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": p.root.as_posix(), "PATH": "/nonexistent"},  # noqa: S603
                               capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            p.close()


class ConfigKeysTest(unittest.TestCase):
    def test_new_keys_are_declared(self) -> None:
        config = json.loads((KIT / "ai-kit.json").read_text(encoding="utf-8"))
        self.assertIn("fix_file", config["commands"])
        self.assertIn("lint_file", config["commands"])
        self.assertIn("{files}", config["commands"]["fix_file"])
        self.assertIn("{files}", config["commands"]["lint_file"])
        self.assertEqual(config["tests"]["summary_regex"], "")
        self.assertEqual(config["tests"]["fast_flags"], [])
        self.assertEqual(config["tests"]["test_dirs"], [])


class InstallerNotesTest(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (INSTALLER / rel).read_text(encoding="utf-8")

    def test_ownership_lists_the_new_scripts(self) -> None:
        text = self.read("reference/ownership.md")
        for name in ("guard_hook.py", "reap.py", "next_change_number.py", "settings_check.py"):
            self.assertIn(name, text)

    def test_doctor_has_the_new_checks(self) -> None:
        text = self.read("reference/doctor.md")
        for needle in ("settings-check", "gates.sh setup", "guard hook", "reap.py", "permission prompt"):
            self.assertIn(needle, text)

    def test_update_notes_the_migration(self) -> None:
        text = self.read("reference/update.md")
        for needle in ("question_lint", "sheet_labels", "interview.md", "fix_file", "summary_regex", "frontmatter"):
            self.assertIn(needle, text)

    def test_no_em_dash(self) -> None:
        for rel in ("SKILL.md", "reference/doctor.md", "reference/update.md", "reference/ownership.md", "reference/install.md"):
            self.assertNotIn("—", self.read(rel), rel)


if __name__ == "__main__":
    unittest.main()
    sys.exit(0)

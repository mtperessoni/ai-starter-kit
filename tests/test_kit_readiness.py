"""Readiness scripts of the kit: hotspots (PC12) and contract snapshots (DS30), against a throwaway project."""

import json
import unittest

from tests.test_kit_scripts import BASH, Project, run, write


class HotspotsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_the_most_changed_large_file_ranks_first(self) -> None:
        big = "src/legacy/billing_engine.py"
        write(self.p.root, big, "x = 1\n" * 600)
        write(self.p.root, "src/legacy/quiet_report.py", "x = 1\n" * 700)
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "legacy", check=True)
        for i in range(3):
            write(self.p.root, big, "x = 1\n" * (600 + i + 1))
            run(self.p.root, "git", "commit", "-q", "-am", f"touch {i}", check=True)
        r = self.p.py("scripts/hotspots.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [line for line in r.stdout.splitlines() if line.startswith("src/")]
        self.assertTrue(rows[0].startswith(big), r.stdout)
        self.assertIn("over limit", rows[0])


class ContractDriftTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        config_path = self.p.root / "ai-kit.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["contracts"] = [{"file": "db/schema.sql", "command": "echo create table orders;"}]
        config_path.write_text(json.dumps(config), encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def test_a_snapshot_equal_to_the_command_output_passes(self) -> None:
        write(self.p.root, "db/schema.sql", "create table orders;\n")
        r = self.p.py("scripts/contract_drift.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_stale_snapshot_fails_and_names_the_file(self) -> None:
        write(self.p.root, "db/schema.sql", "create table carts;\n")
        r = self.p.py("scripts/contract_drift.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("db/schema.sql", r.stdout)

    @unittest.skipUnless(BASH, "bash not available")
    def test_gates_contracts_runs_the_check(self) -> None:
        write(self.p.root, "db/schema.sql", "create table carts;\n")
        r = run(self.p.root, BASH, "scripts/gates.sh", "contracts")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("db/schema.sql", r.stdout)


if __name__ == "__main__":
    unittest.main()

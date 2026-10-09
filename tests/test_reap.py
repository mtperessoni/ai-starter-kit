import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kit" / "scripts"))

import reap  # noqa: E402

SNAP = "snapshot-bash-1760000000000-abc123"
OTHER = "snapshot-bash-1760000099999-zzz999"
ME = 900


def proc(pid, ppid, cmd, age=1.0):
    return {"pid": pid, "ppid": ppid, "cmd": cmd, "age": age}


def wrapper(pid, inner, snap=SNAP, ppid=1, age=1.0):
    return proc(pid, ppid, f'bash -c "source ~/.claude/shell-snapshots/{snap}.sh && eval \'{inner}\'"', age)


def table(*extra):
    return [proc(1, 0, "claude"), wrapper(ME - 1, "scripts/gates.sh reap", ppid=1), proc(ME, ME - 1, "python scripts/reap.py"), *extra]


class Fake:
    def __init__(self, procs):
        self.procs = list(procs)
        self.killed = []

    def list(self):
        return list(self.procs)

    def kill(self, pid):
        self.killed.append(pid)
        dead = {pid}
        grew = True
        while grew:
            grew = False
            for p in self.procs:
                if p["ppid"] in dead and p["pid"] not in dead:
                    dead.add(p["pid"])
                    grew = True
        self.procs = [p for p in self.procs if p["pid"] not in dead]


def reap_with(procs, **kw):
    fake = Fake(procs)
    out = io.StringIO()
    with redirect_stdout(out):
        code = reap.main(kw.pop("argv", []), list_processes=fake.list, kill_tree=fake.kill, self_pid=ME, **kw)
    return fake, out.getvalue(), code


class SessionIdTest(unittest.TestCase):
    def test_the_snapshot_id_comes_from_an_ancestor_command_line(self):
        procs = {p["pid"]: p for p in table()}
        self.assertEqual(reap.session_id(procs, ME), SNAP)

    def test_no_snapshot_in_any_ancestor_gives_none(self):
        procs = {p["pid"]: p for p in [proc(1, 0, "x"), proc(ME, 1, "python reap.py")]}
        self.assertIsNone(reap.session_id(procs, ME))


class SelectionTest(unittest.TestCase):
    def test_a_stdin_waiting_interpreter_of_this_session_is_killed_by_tree(self):
        orphan = wrapper(500, "cat >> tests/a.py <<EOF")
        child = proc(501, 500, "cat")
        fake, out, code = reap_with(table(orphan, child))
        self.assertEqual(fake.killed, [500])
        self.assertIn("reaped: 2", out)
        self.assertIn("left: 0", out)
        self.assertEqual(code, 0)

    def test_python_dash_stdin_child_of_a_session_wrapper_is_killed(self):
        parent = wrapper(500, "python3 - <<'E'")
        child = proc(501, 500, "/c/Python314/python.exe -")
        fake, out, _ = reap_with(table(parent, child))
        self.assertEqual(fake.killed, [500])
        self.assertIn("reaped: 2", out)

    def test_a_process_older_than_the_limit_is_killed_and_a_young_one_is_not(self):
        old = wrapper(500, "pytest -q", age=25.0)
        young = wrapper(510, "pytest -q", age=3.0)
        fake, out, _ = reap_with(table(old, young))
        self.assertEqual(fake.killed, [500])
        self.assertIn("reaped: 1", out)

    def test_older_than_flag_changes_the_limit(self):
        young = wrapper(510, "pytest -q", age=3.0)
        fake, out, _ = reap_with(table(young), argv=["--older-than", "2"])
        self.assertEqual(fake.killed, [510])

    def test_another_session_is_never_touched(self):
        foreign = wrapper(500, "python3 - <<'E'", snap=OTHER, age=90.0)
        fake, out, _ = reap_with(table(foreign))
        self.assertEqual(fake.killed, [])
        self.assertIn("reaped: 0", out)

    def test_never_its_own_ancestors_or_itself(self):
        fake, out, _ = reap_with(table(), argv=["--older-than", "0"])
        self.assertEqual(fake.killed, [])

    def test_never_a_tree_rooted_at_baseline_compare_verify_or_baseline_py(self):
        for inner in ["scripts/gates.sh baseline s1", "scripts/gates.sh compare s1", "scripts/gates.sh verify s1", "python scripts/baseline.py s1"]:
            with self.subTest(inner=inner):
                root = wrapper(500, inner, age=90.0)
                kid = proc(501, 500, "python -", age=90.0)
                fake, out, _ = reap_with(table(root, kid))
                self.assertEqual(fake.killed, [])
                self.assertIn("reaped: 0", out)

    def test_a_protected_descendant_without_the_id_in_its_own_command_line_is_kept(self):
        root = wrapper(500, "scripts/gates.sh verify s1", age=90.0)
        mid = proc(501, 500, "bash scripts/gates.sh verify s1", age=90.0)
        deep = proc(502, 501, "python -m unittest", age=90.0)
        fake, out, _ = reap_with(table(root, mid, deep))
        self.assertEqual(fake.killed, [])

    def test_the_killed_set_is_trees_not_images(self):
        a = wrapper(500, "python3 - <<'E'")
        stray = proc(700, 1, "python.exe other.py", age=90.0)
        fake, out, _ = reap_with(table(a, stray))
        self.assertEqual(fake.killed, [500])
        self.assertIn(700, [p["pid"] for p in fake.procs])

    def test_dry_run_lists_and_kills_nothing(self):
        a = wrapper(500, "python3 - <<'E'")
        fake, out, _ = reap_with(table(a), argv=["--dry-run"])
        self.assertEqual(fake.killed, [])
        self.assertIn("500", out)
        self.assertIn("reaped: 0", out)

    def test_survivors_are_listed_and_exit_1(self):
        a = wrapper(500, "python3 - <<'E'")
        fake = Fake(table(a))
        fake.kill = lambda pid: fake.killed.append(pid)
        out = io.StringIO()
        with redirect_stdout(out):
            code = reap.main([], list_processes=fake.list, kill_tree=fake.kill, self_pid=ME)
        self.assertEqual(code, 1)
        self.assertIn("reaped: 0", out.getvalue())
        self.assertIn("left: 1", out.getvalue())
        self.assertIn("500", out.getvalue())

    def test_without_a_snapshot_id_nothing_is_killed(self):
        fake, out, code = reap_with([proc(1, 0, "x"), proc(ME, 1, "python reap.py"), proc(500, 1, "python -", age=99.0)])
        self.assertEqual(fake.killed, [])
        self.assertIn("reaped: 0", out)
        self.assertEqual(code, 0)


class ParseTest(unittest.TestCase):
    def test_posix_ps_output_is_parsed(self):
        rows = reap.parse_ps("  10     1   90 bash -c source snapshot-x.sh\n  11    10 12000 python -\n")
        self.assertEqual(rows[0], {"pid": 10, "ppid": 1, "age": 1.5, "cmd": "bash -c source snapshot-x.sh"})
        self.assertEqual(rows[1]["age"], 200.0)

    def test_windows_json_one_object_or_a_list(self):
        one = reap.parse_cim('{"pid":4,"ppid":1,"age":2.5,"cmd":null}')
        self.assertEqual(one, [{"pid": 4, "ppid": 1, "age": 2.5, "cmd": ""}])
        many = reap.parse_cim('[{"pid":4,"ppid":1,"age":0,"cmd":"a"},{"pid":5,"ppid":4,"age":1,"cmd":"b"}]')
        self.assertEqual([r["pid"] for r in many], [4, 5])

    def test_real_listing_contains_this_process(self):
        pids = [p["pid"] for p in reap.list_processes()]
        self.assertIn(os.getpid(), pids)


if __name__ == "__main__":
    unittest.main()

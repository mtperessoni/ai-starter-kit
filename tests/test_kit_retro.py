"""Retro (RT09 to RT13): synthetic events and resources built from the RT04 and RT07 schemas."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1] / "kit"
sys.path.insert(0, str(KIT / "scripts"))

import retro  # noqa: E402
import retro_detectors as det  # noqa: E402

SID = "abcdef12"
FULL_SID = "abcdef12-0000-4000-8000-000000000001"
T0 = 1_700_000_000.0


class Log:
    """Builds an events list; time advances by the stated gap."""

    def __init__(self):
        self.ev, self.t, self.n = [], T0, 0

    def add(self, ev, gap=1.0, **kw):
        self.t += gap
        self.ev.append({"ts": self.t, "ev": ev, "sid": SID, "agent": kw.pop("agent", "main"), **kw})
        return len(self.ev)

    def call(self, tool="Bash", cls="shell", dur=1.0, agent="main", err=False, cmd="ls", **kw):
        self.n += 1
        tuid = f"tu{self.n}"
        h = kw.pop("h", f"h{self.n}")
        self.add("PreToolUse", agent=agent, tool=tool, tuid=tuid, cls=cls, cmd=cmd, h=h)
        extra = {"err": True} if err else {}
        return self.add("PostToolUseFailure" if err else "PostToolUse", gap=dur, agent=agent, tool=tool, tuid=tuid,
                        cls=cls, cmd=cmd, h=h, ms=int(dur * 1000), **extra, **kw)

    def subagent(self, aid, minutes=1.0, tokens=1000, tools=3, tp=None, atype="general-purpose"):
        self.add("SubagentStart", agent=aid, atype=atype)
        self.add("SubagentStop", gap=minutes * 60, agent=aid, atype=atype, **({"tp": tp} if tp else {}))
        return self.add("PostToolUse", tool="Agent", tuid=f"ag{aid}", cls="agent", ms=int(minutes * 60000),
                        sub={"tokens": tokens, "ms": int(minutes * 60000), "tools": tools, "status": "completed", "id": aid})


def project(events, probes=(), cfg=None, ctx="ctx"):
    root = Path(tempfile.mkdtemp())
    run = root / ".ai-kit" / "runs" / ctx
    run.mkdir(parents=True)
    (run / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    (run / "resources.jsonl").write_text("".join(json.dumps(p) + "\n" for p in probes), encoding="utf-8")
    if cfg is not None:
        (root / "ai-kit.json").write_text(json.dumps({"telemetry": cfg}), encoding="utf-8")
    return root


def findings(root, ctx="ctx"):
    s = retro.analyze(root, ctx)
    return {f["id"]: f for f in s["findings"]}, s


def clean_log():
    log = Log()
    log.add("SessionStart")
    log.call(cls="test.related", cmd="gates.sh related")
    log.call(tool="Edit", cls="edit", files=["a.py"])
    log.subagent("ag1")
    log.add("SessionEnd")
    return log


class DetectorTests(unittest.TestCase):
    def test_clean_run_has_no_finding(self):
        root = project(clean_log().ev, [{"ts": T0, "label": "related", "sec": 2, "mem_peak_mb": 100}])
        f, _ = findings(root)
        self.assertEqual(f, {})
        md = (root / ".ai-kit/runs/ctx/retro.md").read_text(encoding="utf-8")
        self.assertIn("No finding", md)
        self.assertEqual([h for h in ("## Coverage", "## Findings", "## Time and tokens", "## Top 5") if h not in md], [])

    def test_long_call(self):
        log = Log()
        seq = log.call(dur=400, cmd="sleep 400")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["long_call"]["evidence"]["seq"], [seq])
        self.assertEqual(f["long_call"]["evidence"]["cmd"], "sleep 400")
        self.assertEqual(f["long_call"]["threshold"], 300)

    def test_slow_test(self):
        log = Log()
        seq = log.call(cls="test.single", dur=50, cmd="pytest x")
        f, _ = findings(project(log.ev, cfg={"long_test_s": 10}))
        self.assertEqual(f["slow_test"]["evidence"]["seq"], [seq])
        self.assertNotIn("long_call", f)

    def test_full_suite_mid_task(self):
        log = Log()
        seq = log.call(cls="test.full", agent="ag1", cmd="gates.sh full")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["full_suite_mid_task"]["evidence"]["seq"][0], seq - 1)
        self.assertEqual(f["full_suite_mid_task"]["evidence"]["agent"], "ag1")

    def test_two_full_suites_in_main(self):
        log = Log()
        log.call(cls="test.full")
        log.call(cls="test.full")
        f, _ = findings(project(log.ev))
        self.assertEqual(len(f["full_suite_mid_task"]["evidence"]["seq"]), 1)

    def test_long_subagent(self):
        log = Log()
        log.subagent("ag1", minutes=40)
        f, _ = findings(project(log.ev))
        self.assertEqual(f["long_subagent"]["evidence"]["agent"], "ag1")
        self.assertGreaterEqual(f["long_subagent"]["value"], 39)

    def test_heavy_subagent_tokens_and_tools(self):
        log = Log()
        log.subagent("ag1", tokens=200000, tools=60)
        _, s = findings(project(log.ev))
        heavy = [x for x in s["findings"] if x["id"] == "heavy_subagent"]
        self.assertEqual(sorted(x["value"] for x in heavy), [60, 200000])

    def test_auto_compaction(self):
        log = Log()
        seq = log.add("PreCompact", trigger="auto", ctx_before=190000)
        log.add("PreCompact", trigger="manual")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["auto_compaction"]["evidence"]["seq"], [seq])

    def test_big_output(self):
        log = Log()
        seq = log.call(out_kb=500, cmd="cat big")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["big_output"]["evidence"]["seq"], [seq])

    def test_loop_same_failing_input(self):
        log = Log()
        seqs = [log.call(err=True, h="same", cmd="make") for _ in range(3)]
        f, _ = findings(project(log.ev))
        self.assertEqual(f["loop"]["evidence"]["seq"], seqs)

    def test_loop_same_file_edited(self):
        log = Log()
        for _ in range(8):
            log.call(tool="Edit", cls="edit", files=["a.py"], cmd="a.py")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["loop"]["value"], 8)
        self.assertEqual(f["loop"]["evidence"]["cmd"], "a.py")

    def test_error_rate_needs_twenty_calls(self):
        log = Log()
        for _ in range(10):
            log.call(err=True)
        f, _ = findings(project(log.ev, cfg={"loop_repeats": 99}))
        self.assertNotIn("error_rate", f)
        for _ in range(10):
            log.call()
        f, _ = findings(project(log.ev, cfg={"loop_repeats": 99}))
        self.assertEqual(f["error_rate"]["value"], 0.5)

    def test_memory_and_disk_drop(self):
        probes = [{"ts": T0, "label": "full", "sec": 5, "mem_peak_mb": 3000, "disk_free_gb_before": 50, "disk_free_gb_after": 48}]
        f, _ = findings(project(Log().ev, probes))
        self.assertEqual(f["memory"]["value"], 3000)
        self.assertEqual(f["memory"]["evidence"]["cmd"], "full")
        self.assertEqual(f["disk_drop"]["value"], 2048)

    def test_docker_outside_gates(self):
        log = Log()
        seq = log.call(cls="docker.build", cmd="docker build .")
        log.call(cls="docker.build", cmd="bash scripts/gates.sh build")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["docker_outside_gates"]["evidence"]["seq"], [seq - 1])

    def test_unbounded_background(self):
        log = Log()
        seq = log.call(cls="background.unbounded", cmd="tail -f log")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["unbounded_background"]["evidence"]["seq"], [seq - 1])

    def test_killed_call(self):
        log = Log()
        log.n += 1
        seq = log.add("PreToolUse", tool="Bash", tuid="lost", cls="shell", cmd="hang")
        log.add("SessionEnd")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["killed_call"]["evidence"]["seq"], [seq])

    def test_dead_files_scoped_to_this_run(self):
        temp = Path(tempfile.mkdtemp())
        mine = temp / "claude" / "proj" / FULL_SID / "tasks"
        other = temp / "claude" / "proj" / "99999999-other" / "tasks"
        for d in (mine, other):
            d.mkdir(parents=True)
            (d / "out.txt").write_bytes(b"x" * 3000)
        log = Log()
        log.add("SessionStart", tp=f"C:\\x\\{FULL_SID}.jsonl")
        root = project(log.ev)
        run = retro.load_run(root / ".ai-kit/runs/ctx", root)
        th = dict(det.DEFAULTS, dead_mb=0.001)
        got = list(det.dead_files(run, th, temp=temp, worktrees=lambda r: []))
        self.assertEqual(len(got), 1)
        self.assertIn(FULL_SID, got[0]["evidence"]["cmd"])
        self.assertNotIn("99999999", got[0]["evidence"]["cmd"])
        # only another session's junk: no finding
        run["session_ids"] = {"zzzzzzzz"}
        self.assertEqual(list(det.dead_files(run, th, temp=temp, worktrees=lambda r: [])), [])

    def test_dead_files_missing_worktree_listed(self):
        temp = Path(tempfile.mkdtemp())
        big = temp / "claude" / "p" / SID / "tasks"
        big.mkdir(parents=True)
        (big / "o").write_bytes(b"x" * 3000)
        log = Log()
        log.add("SessionStart")
        root = project(log.ev)
        run = retro.load_run(root / ".ai-kit/runs/ctx", root)
        th = dict(det.DEFAULTS, dead_mb=0.001)
        got = list(det.dead_files(run, th, temp=temp, worktrees=lambda r: [Path("main"), temp / "gone"]))
        self.assertIn("missing", got[0]["evidence"]["cmd"])


class SpansAndCoverageTests(unittest.TestCase):
    def test_human_wait_excluded_from_long_call_and_agent_work(self):
        log = Log()
        log.add("SessionStart")
        log.call(tool="AskUserQuestion", cls="wait.human", dur=600)
        log.add("Notification", ntype="permission_prompt")
        log.add("PreToolUse", gap=400, tool="Bash", tuid="x", cls="shell", cmd="slow")
        log.add("PostToolUse", gap=10, tool="Bash", tuid="x", cls="shell", cmd="slow", ms=410000)
        f, s = findings(project(log.ev))
        self.assertNotIn("long_call", f)
        self.assertGreaterEqual(s["totals"]["human_wait_s"], 1000)
        self.assertLess(s["totals"]["agent_work_s"], 50)

    def test_coverage_numbers(self):
        log = Log()
        log.add("SessionStart", ver="2.1.178")
        log.call()
        log.add("PostToolUse", tool="Bash", tuid="nodur", cls="shell")
        log.subagent("ag1", tokens=500)
        log.subagent("ag2", tokens=500)
        log.ev[-1]["sub"].pop("tokens")
        _, s = findings(project(log.ev, [{"ts": T0, "label": "x", "sec": 1}]))
        c = s["coverage"]
        self.assertEqual(c["calls_with_duration_pct"], 75)
        self.assertEqual(c["subagents_with_tokens_pct"], 50)
        self.assertEqual((c["probes"], c["version"], c["main_tokens_covered"]), (1, "2.1.178", False))

    def test_transcript_enrichment_dedupes_by_request(self):
        tp = Path(tempfile.mkdtemp()) / "t.jsonl"
        use = lambda i, o, r, c, th=0: {"input_tokens": i, "output_tokens": o, "cache_read_input_tokens": r,  # noqa: E731
                                        "cache_creation_input_tokens": c, "output_tokens_details": {"thinking_tokens": th}}
        lines = [
            {"type": "assistant", "requestId": "r1", "timestamp": "2026-10-05T10:00:00Z", "message": {"usage": use(10, 5, 100, 20)}},
            {"type": "assistant", "requestId": "r1", "message": {"usage": use(10, 7, 100, 20, 3)}},
            {"type": "assistant", "requestId": "r2", "message": {"usage": use(1, 2, 300000, 0)}},
            {"type": "user", "tool_use_id": "t", "is_error": False},
            {"garbage": True},
        ]
        tp.write_text("\n".join(json.dumps(x) for x in lines) + "\nnot json\n", encoding="utf-8")
        log = Log()
        log.add("SessionStart", tp=str(tp))
        log.call()
        f, s = findings(project(log.ev))
        self.assertEqual(s["totals"]["tokens_main"], (10 + 7 + 20) + (1 + 2))
        self.assertEqual(s["totals"]["context_peak"], 300001)
        self.assertEqual(f["context_peak"]["value"], 300001)
        self.assertTrue(s["coverage"]["main_tokens_covered"])

    def test_unreadable_transcript_marked_not_covered(self):
        log = Log()
        log.add("SessionStart", tp="Z:\\nowhere\\x.jsonl")
        _, s = findings(project(log.ev))
        self.assertFalse(s["coverage"]["main_tokens_covered"])
        self.assertIsNone(s["totals"]["tokens_main"])

    def test_missing_sources_do_not_raise(self):
        root = Path(tempfile.mkdtemp())
        rc = retro.main(["--root", str(root), "--context", "none"])
        self.assertEqual(rc, 0)


class OutputsTests(unittest.TestCase):
    def test_outputs_and_copy_into_change_folder(self):
        root = project(clean_log().ev, ctx="001-demo")
        (root / "changes" / "001-demo").mkdir(parents=True)
        retro.analyze(root, "001-demo")
        run = root / ".ai-kit/runs/001-demo"
        for n in ("spans.jsonl", "summary.json", "retro.md"):
            self.assertTrue((run / n).is_file(), n)
        self.assertEqual((root / "changes/001-demo/retro.md").read_text(encoding="utf-8"), (run / "retro.md").read_text(encoding="utf-8"))
        kinds = {json.loads(line)["kind"] for line in (run / "spans.jsonl").read_text().splitlines()}
        self.assertEqual(kinds, {"main", "subagent"})

    def test_slug_context_matches_numbered_folder(self):
        root = project(clean_log().ev, ctx="demo")
        (root / "changes" / "007-demo").mkdir(parents=True)
        retro.analyze(root, "demo")
        self.assertTrue((root / "changes/007-demo/retro.md").is_file())

    def test_no_copy_without_change_folder(self):
        root = project(clean_log().ev)
        retro.analyze(root, "ctx")
        self.assertFalse((root / "changes").exists())

    def test_cli_prints_at_most_15_lines_and_exits_0(self):
        root = project(clean_log().ev)
        r = subprocess.run([sys.executable, str(KIT / "scripts/retro.py"), "--root", str(root), "--context", "ctx"],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0)
        self.assertLessEqual(len(r.stdout.splitlines()), 15)

    def test_thresholds_default_and_override(self):
        root = Path(tempfile.mkdtemp())
        self.assertEqual(retro.thresholds(root)["long_call_s"], 300)
        (root / "ai-kit.json").write_text(json.dumps({"telemetry": {"long_call_s": 5}}), encoding="utf-8")
        th = retro.thresholds(root)
        self.assertEqual((th["long_call_s"], th["keep_days"]), (5, 14))

    def test_truncate_drops_oldest_half(self):
        log = Log()
        for _ in range(200):
            log.call()
        root = project(log.ev, cfg={"max_events_mb": 0.01})
        retro.analyze(root, "ctx")
        lines = (root / ".ai-kit/runs/ctx/events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(json.loads(lines[0])["ev"], "truncated")
        self.assertLess(len(lines), 300)


class FoundInTheRealEvaluation(unittest.TestCase):
    """Defects the 2026-10-05 telemetry evaluation exposed in a real session with subagents."""

    def test_two_events_written_on_one_line_are_both_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text('{"seq": 1, "ev": "a"}{"seq": 2, "ev": "b"}\n{"seq": 3, "ev": "c"}\nnot json\n',
                            encoding="utf-8")
            self.assertEqual([e["seq"] for e in retro.jsonl(path)], [1, 2, 3])

    def test_the_default_big_output_is_below_what_claude_code_returns(self):
        """Claude Code cuts a tool output near 30 KB before the model sees it."""
        self.assertLess(det.DEFAULTS["big_output_kb"], 29)


class PruneTests(unittest.TestCase):
    def test_prune_by_age_and_archived(self):
        root = project(clean_log().ev, ctx="old")
        runs = root / ".ai-kit/runs"
        for name in ("fresh", "arch"):
            (runs / name).mkdir()
            (runs / name / "events.jsonl").write_text("{}\n")
        (runs / "current").write_text("fresh\n")
        (root / "changes/archive/003-arch").mkdir(parents=True)
        old = time.time() - 20 * 86400
        for p in (runs / "old").rglob("*"):
            os.utime(p, (old, old))
        gone = retro.prune(root, 14)
        self.assertEqual(sorted(gone), ["arch", "old"])
        self.assertTrue((runs / "fresh").exists())
        self.assertTrue((runs / "current").exists())

    def test_prune_cli(self):
        root = project(clean_log().ev)
        r = subprocess.run([sys.executable, str(KIT / "scripts/retro.py"), "--root", str(root), "--prune"],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0)
        self.assertIn("pruned 0", r.stdout)


class DocReadsTests(unittest.TestCase):
    def reads(self, paths, cfg=None, files=None):
        log = Log()
        for path in paths:
            log.call(tool="Read", cls="read", cmd=path)
        root = project(log.ev, cfg=cfg)
        for rel, size in (files or {}).items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"x" * size)
        return findings(root)

    def test_a_doc_read_past_the_threshold_is_flagged_with_rereads_and_bytes(self):
        f, _ = self.reads(["docs/prd/a.md"] * 4 + ["src/app.py"], files={"docs/prd/a.md": 100})
        d = f["doc_reads"]
        self.assertEqual(d["value"], 4)
        self.assertEqual(d["threshold"], 3)
        self.assertIn("docs/prd/a.md", d["evidence"]["cmd"])
        self.assertIn("rereads 3", d["evidence"]["cmd"])
        self.assertIn("400 bytes", d["evidence"]["cmd"])
        self.assertNotIn("app.py", d["evidence"]["cmd"])

    def test_reads_at_the_threshold_are_not_flagged(self):
        f, _ = self.reads(["docs/prd/a.md"] * 3 + [".claude/skills/x/SKILL.md", "changes/001-x/plan.md"])
        self.assertNotIn("doc_reads", f)

    def test_the_threshold_comes_from_the_config(self):
        f, _ = self.reads(["docs/prd/a.md"] * 2, cfg={"doc_reads": 1})
        self.assertEqual(f["doc_reads"]["threshold"], 1)

    def test_only_the_top_five_are_listed(self):
        paths = [f"docs/f{i}.md" for i in range(7)] * 2 + ["docs/f0.md"] * 3
        f, _ = self.reads(paths, cfg={"doc_reads": 1})
        self.assertEqual(f["doc_reads"]["evidence"]["cmd"].count("docs/f"), 5)


class KpiTests(unittest.TestCase):
    def run_of(self, log, cfg=None):
        root = project(log.ev, cfg=cfg)
        return retro.load_run(root / ".ai-kit/runs/ctx", root), root

    def test_values_count_main_calls_agents_by_role_and_inline_reads(self):
        log = Log()
        log.call(tool="Read", cls="read", cmd="docs/a.md")
        log.call(tool="Read", cls="read", cmd="docs/b.md")
        log.subagent("s1", atype="prd-flow-surveyor")
        log.call(tool="Read", cls="read", cmd="docs/c.md")
        log.subagent("e1", atype="prd-flow-executor")
        log.subagent("e2", atype="prd-flow-executor")
        run, _ = self.run_of(log)
        k = det.kpi_values(run)
        self.assertEqual(k["main_calls"], 6)
        self.assertEqual(k["inline_reads"], 2)
        self.assertEqual(k["agents_by_role"], {"prd-flow-surveyor": 1, "prd-flow-executor": 2})

    def test_inline_reads_is_none_without_a_surveyor(self):
        log = Log()
        log.call(tool="Read", cls="read", cmd="docs/a.md")
        run, _ = self.run_of(log)
        self.assertIsNone(det.kpi_values(run)["inline_reads"])

    def test_gate_runs_are_split_by_thread(self):
        log = Log()
        log.call(cmd="python .claude/skills/prd-flow/scripts/gate.py --rules x")
        log.call(cmd="scripts/gates.sh compare demo")
        log.call(cmd="scripts/gates.sh related", agent="e1")
        run, _ = self.run_of(log)
        k = det.kpi_values(run)
        self.assertEqual((k["gate_runs_main"], k["gate_runs_sub"]), (2, 1))

    def test_parallel_factor_is_agent_time_over_the_window(self):
        log = Log()
        log.add("SubagentStart", agent="a", atype="prd-flow-executor")
        log.add("SubagentStart", agent="b", atype="prd-flow-executor")
        log.add("SubagentStop", gap=60, agent="a", atype="prd-flow-executor")
        log.add("SubagentStop", gap=0, agent="b", atype="prd-flow-executor")
        run, _ = self.run_of(log)
        self.assertAlmostEqual(det.kpi_values(run)["parallel_factor"], 2.0, places=1)

    def test_a_kpi_past_its_target_is_flagged_from_the_config(self):
        log = Log()
        for _ in range(4):
            log.call()
        root = project(log.ev, cfg={"kpi_main_calls": 3})
        f, s = findings(root)
        self.assertEqual(f["kpi_main_calls"]["value"], 4)
        self.assertEqual(f["kpi_main_calls"]["threshold"], 3)
        self.assertIn("kpis", s)

    def test_inline_reads_above_target_and_low_parallelism_are_flagged(self):
        log = Log()
        log.call(tool="Read", cls="read", cmd="docs/a.md")
        log.subagent("s1", atype="prd-flow-surveyor")
        log.subagent("e1", atype="prd-flow-executor")
        log.subagent("e2", atype="prd-flow-executor")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["kpi_inline_reads"]["value"], 1)
        self.assertIn("kpi_parallel_factor", f)

    def test_a_run_within_every_target_has_no_kpi_finding(self):
        f, _ = findings(project(clean_log().ev))
        self.assertFalse([k for k in f if k.startswith("kpi_")])


class RunSpeedDetectorTests(unittest.TestCase):
    def test_polling_calls_are_flagged(self):
        log = Log()
        a = log.call(cls="wait.test", cmd="until grep -q done out.txt; do sleep 5; done", dur=30)
        b = log.call(cls="wait.test", cmd="while true; do\n  tail -1 out.txt\n  sleep 5\ndone", dur=30)
        c = log.call(cls="wait.test", cmd="for i in 1 2 3; do ls out.txt && sleep 2; done", dur=30)
        log.call(cls="wait.test", cmd="scripts/gates.sh baseline x", dur=30)
        f, _ = findings(project(log.ev))
        self.assertEqual(f["poll_calls"]["value"], 3)
        self.assertEqual(f["poll_calls"]["evidence"]["seq"], [a, b, c])

    def test_a_bare_sleep_or_seq_is_not_a_poll(self):
        log = Log()
        log.call(cls="wait.test", cmd="sleep 30", dur=30)
        log.call(cls="wait.test", cmd="seq 1 5", dur=30)
        log.call(cls="wait.test", cmd="for f in a b; do echo $f; done; sleep 5", dur=30)
        log.call(cls="wait.test", cmd="echo ready && sleep 2 && echo go", dur=30)
        f, _ = findings(project(log.ev))
        self.assertNotIn("poll_calls", f)

    def test_background_alive_at_handback(self):
        log = Log()
        log.add("SubagentStart", agent="ag1", atype="x")
        seq = log.add("SubagentStop", agent="ag1", atype="x", bg=2)
        log.add("SubagentStart", agent="ag2", atype="x")
        log.add("SubagentStop", agent="ag2", atype="x", bg=0)
        f, _ = findings(project(log.ev))
        self.assertEqual((f["bg_alive_at_return"]["value"], f["bg_alive_at_return"]["evidence"]["seq"]), (2, [seq]))

    def test_long_bash_without_timeout(self):
        log = Log()
        seq = log.call(dur=150, cmd="make", auto_bg=True)
        log.call(dur=150, cmd="make", timeout=600000)
        f, _ = findings(project(log.ev))
        self.assertEqual(f["no_timeout"]["evidence"]["seq"], [seq])
        self.assertEqual(f["no_timeout"]["value"], 1)

    def test_baseline_inside_a_non_chief_agent(self):
        log = Log()
        log.call(cmd="scripts/gates.sh baseline s", agent="main")
        seq = log.call(cmd="scripts/gates.sh baseline s", agent="ag1")
        f, _ = findings(project(log.ev))
        self.assertEqual(f["baseline_in_agent"]["evidence"]["seq"], [seq])
        self.assertEqual(f["baseline_in_agent"]["evidence"]["agent"], "ag1")

    def test_chief_generation_time_in_the_report(self):
        log = Log()
        log.add("SessionStart")
        log.call(dur=10)
        log.add("Stop", gap=100)
        f, s = findings(project(log.ev))
        self.assertAlmostEqual(s["totals"]["chief_gen_s"], 100.0, delta=5)
        md = retro.render("c", s)
        self.assertIn("chief_gen_s", md)

    def test_ask_wait_uses_wait_ms_when_present(self):
        log = Log()
        log.add("PreToolUse", tool="AskUserQuestion", tuid="q", cls="wait.human")
        log.add("PostToolUse", gap=60, tool="AskUserQuestion", tuid="q", cls="wait.human", ms=1, wait_ms=60000)
        _, s = findings(project(log.ev))
        self.assertAlmostEqual(s["totals"]["human_wait_s"], 60.0, delta=1)


if __name__ == "__main__":
    unittest.main()

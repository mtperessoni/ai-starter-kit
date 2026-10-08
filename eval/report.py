"""Scorecard and adoption decision from `<arm>-<scenario>-r<n>.metrics.json` (decision rule of README)."""
import json
import re
import statistics
import sys
from pathlib import Path

import six

CAND, BASE = "LT", "SK"
EXPECTED_REPS = {"S1": 2, "S2": 2, "S3": 1, "S4": 1}
INFRA = {"rate_limited", "skipped_rate_limit", "build_failed"}
NAME = re.compile(r"^(?P<arm>[^-]+(?:-[A-Z]+)*)-(?P<sc>[A-Z]\d+)-r(?P<n>\d+)$")
LOWER, HIGHER = "lower", "higher"
GROUP_LABELS = {"source_fidelity": "Source-of-truth fidelity"}
GROUPS = {
    "tokens": {"tokens_total": LOWER, "context_peak": LOWER},
    "speed": {"wall_min": LOWER, "min_to_code": LOWER, "turns": LOWER},
    "efficiency": {"cost_usd": LOWER, "cost_per_accept": LOWER, "doc_bytes": LOWER},
    "rework": {"rework_commits": LOWER, "kit_self_fixes": LOWER},
    "plan_fidelity": {"plan_coverage": HIGHER, "plan_drift": LOWER},
    "source_fidelity": {"traceability": HIGHER, "docs_first": HIGHER, "promoted": HIGHER,
                        "single_source": LOWER, "conflict_found": HIGHER,
                        "contradiction_left": LOWER, "gap_recorded": HIGHER},
    "errors": {"tool_errors": LOWER, "error_rate": LOWER},
    "subagents": {"subagent_tokens_median": LOWER, "subagent_errors": LOWER,
                  "subagents_wasted": LOWER, "tasks_per_executor": HIGHER},
    "reviews": {"review_rounds": LOWER, "review_fix_commits": LOWER,
                "blind_findings_total": LOWER, "blind_approve": HIGHER},
    "code_quality": {"accept": HIGHER, "suite_green": HIGHER, "blind_bugs": LOWER,
                     "blind_critical": LOWER, "blind_high": LOWER},
}
# Efficiency analysis: question -> (title, {metric: direction or None when it only describes})
QUESTIONS = {
    "X1": ("Token consumption", {"tokens_total": LOWER, "tokens_main": LOWER,
                                 "tokens_subagents": LOWER, "context_peak": LOWER,
                                 "cost_usd": LOWER}),
    "X2": ("Efficiency of the subagents", {
        "subagents": None, "subagent_tokens_median": LOWER, "subagent_tool_calls_median": LOWER,
        "subagent_errors": LOWER, "subagents_wasted": LOWER, "tasks_per_executor": HIGHER,
        "subagent_token_share": None}),
    "X3": ("Error rate during implementation", {
        "tool_calls": None, "tool_errors": LOWER, "error_rate": LOWER, "test_runs": None,
        "failed_test_runs": LOWER, "kit_self_fixes": LOWER}),
    "X4": ("Time to complete", {"wall_min": LOWER, "min_to_code": LOWER, "min_per_task": LOWER}),
    "X5": ("Reviews needed for good code", {
        "review_rounds": LOWER, "review_fix_commits": LOWER, "blind_findings_total": LOWER}),
    "X6": ("Code with fewest problems", {
        "accept": HIGHER, "suite_green": HIGHER, "blind_bugs": LOWER, "blind_critical": LOWER,
        "blind_high": LOWER, "blind_medium": LOWER, "blind_low": LOWER, "blind_approve": HIGHER}),
}
SIZES = ("S", "M", "L")
GATE_ONLY = ["accept", "suite_green", "gate_ok", "completed", "prd_fidelity", "protocol_adherence"]
REPORT_ONLY = ["subagents", "subagent_token_share"] + [
    k for _, ms in QUESTIONS.values() for k in ms]
SPEED_KEYS = ("tokens_total", "cost_usd", "wall_min")
F1_SLACK = 0.05
BAND = 0.10


def load(results):
    """{arm: {scenario: [metrics, ...]}}; files that do not parse are skipped."""
    runs = {}
    for f in sorted(Path(results).glob("*.metrics.json")):
        m = NAME.match(f.name[: -len(".metrics.json")])
        if not m:
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("status") not in INFRA:
            runs.setdefault(m["arm"], {}).setdefault(m["sc"], []).append(data)
    return runs


def values(runs, key):
    out = []
    for m in runs:
        v = m.get(key)
        if isinstance(v, bool):
            v = float(v)
        if isinstance(v, (int, float)):
            out.append(float(v))
    return out


def median(vals):
    return statistics.median(vals) if vals else None


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def compare(key, direction, cand_runs, base_runs):
    """win, loss or tie; None when either side has no value (never decided on missing data)."""
    cv, bv = values(cand_runs, key), values(base_runs, key)
    if not cv or not bv:
        return None, None, None, None
    c, b = median(cv), median(bv)
    spread = max(max(v) - min(v) for v in (cv, bv))
    band = max(BAND * abs(b), spread)
    diff = c - b if direction == HIGHER else b - c
    verdict = "win" if diff > band else "loss" if diff < -band else "tie"
    return verdict, c, b, band


def gates(data, cand_arm=CAND, base_arm=BASE):
    cand = [m for s in data.get(cand_arm, {}).values() for m in s]
    base = [m for s in data.get(base_arm, {}).values() for m in s]
    out = []

    def add(rule, ok, detail):
        out.append({"rule": rule, "ok": bool(ok), "detail": detail})

    ca, ba = mean(values(cand, "accept")), mean(values(base, "accept"))
    add(f"Q1 accept: {cand_arm} mean at least {base_arm}", ca is not None and (ba is None or ca >= ba),
        f"{cand_arm} {ca}, {base_arm} {ba}")
    for key, label in (("suite_green", "Q2"), ("gate_ok", "Q3"), ("completed", "Q4")):
        ok = bool(cand) and all(m.get(key) is True for m in cand)
        add(f"{label} {key}: true in every {cand_arm} run", ok,
            f"{sum(1 for m in cand if m.get(key) is True)} of {len(cand)}")
    cf, bf = mean(values(cand, "prd_fidelity")), mean(values(base, "prd_fidelity"))
    add(f"F1 prd_fidelity: {cand_arm} at least {base_arm} minus 0.05",
        cf is not None and (bf is None or cf >= bf - F1_SLACK), f"{cand_arm} {cf}, {base_arm} {bf}")
    add(f"R4 protocol_adherence: 1.0 in every {cand_arm} run",
        bool(cand) and all(m.get("protocol_adherence") == 1.0 for m in cand),
        f"{sum(1 for m in cand if m.get('protocol_adherence') == 1.0)} of {len(cand)}")
    return out


def scorecard(data, cand_arm=CAND, base_arm=BASE):
    cards = {}
    for sc in sorted(set(data.get(cand_arm, {})) | set(data.get(base_arm, {}))):
        cr, br = data.get(cand_arm, {}).get(sc, []), data.get(base_arm, {}).get(sc, [])
        row = {}
        for group, metrics in GROUPS.items():
            for key, direction in metrics.items():
                v, c, b, band = compare(key, direction, cr, br)
                row[key] = {"group": group, "verdict": v, "lt": c, "sk": b, "band": band}
        cards[sc] = row
    return cards


def tally(cards):
    t = {g: {"win": 0, "loss": 0, "tie": 0} for g in GROUPS}
    for row in cards.values():
        for cell in row.values():
            if cell["verdict"]:
                t[cell["group"]][cell["verdict"]] += 1
    return t


def evaluate(data, base=BASE, cand=CAND):
    gate_list = gates(data, cand, base)
    cards = scorecard(data, cand, base)
    tl = tally(cards)
    speed_ok = True
    speed_detail = {}
    for sc in ("S1", "S2"):
        for key in SPEED_KEYS:
            v = cards.get(sc, {}).get(key, {}).get("verdict")
            speed_detail[f"{sc}.{key}"] = v
            speed_ok = speed_ok and v in ("win", "tie")
    groups_ok = all(t["loss"] <= t["win"] for t in tl.values())
    gates_ok = all(g["ok"] for g in gate_list)
    work = [{"scenario": sc, "metric": k, "group": c["group"], "lt": c["lt"], "sk": c["sk"]}
            for sc, row in cards.items() for k, c in row.items() if c["verdict"] == "loss"]
    adopt = gates_ok and speed_ok and groups_ok
    return {"gates": gate_list, "gates_ok": gates_ok, "scorecard": cards, "tally": tl,
            "speed": speed_detail, "speed_ok": speed_ok, "groups_ok": groups_ok,
            "adopt": adopt, "work_list": work}


def expected_reps(cfg):
    """{scenario: reps} from a config dict; the small-suite map when there is no config."""
    if not cfg:
        return dict(EXPECTED_REPS)
    return {sc: int(spec["reps"]) for sc, spec in cfg["scenarios"].items()}


def derive_reps(results):
    """Highest repetition number found per scenario, when no config is given."""
    reps = {}
    for f in sorted(Path(results).glob("*.metrics.json")):
        m = NAME.match(f.name[: -len(".metrics.json")])
        if m:
            reps[m["sc"]] = max(reps.get(m["sc"], 0), int(m["n"]))
    return reps


def run_counts(data, base=BASE, cand=CAND, reps=None):
    counts = {}
    for arm in (base, cand):
        for sc, want in (reps or EXPECTED_REPS).items():
            have = len(data.get(arm, {}).get(sc, []))
            counts[f"{arm}.{sc}"] = {"found": have, "expected": want, "missing": max(0, want - have)}
    return counts


def medians(data):
    out = {}
    keys = [k for g in GROUPS.values() for k in g] + GATE_ONLY + REPORT_ONLY
    for arm, scs in data.items():
        for sc, runs in scs.items():
            out.setdefault(sc, {})[arm] = {k: median(values(runs, k)) for k in keys}
    return out


def fmt(v):
    if v is None:
        return "n/a"
    return f"{v:.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def ranks(medians_by_arm, direction):
    """1 is best; equal medians share a rank; arms without a value or metrics without a direction are left out."""
    vals = {a: v for a, v in medians_by_arm.items() if v is not None}
    if direction is None:
        return {}
    ordered = sorted(vals.values(), reverse=direction == HIGHER)
    return {a: ordered.index(v) + 1 for a, v in vals.items()}


def analyze(data, sizes=None):
    """X1 to X6: per metric the median per arm over all runs and per scenario size, plus each arm's rank."""
    sizes = sizes or {}
    arms = sorted(data)
    out = {}
    for qid, (title, metrics) in QUESTIONS.items():
        rows = {}
        for key, direction in metrics.items():
            scopes = {"all": lambda sc: True}
            scopes.update({z: (lambda sc, z=z: sizes.get(sc) == z) for z in SIZES})
            row = {"direction": direction}
            for scope, pick in scopes.items():
                med = {a: median(values([m for sc, runs in data[a].items() if pick(sc) for m in runs], key))
                       for a in arms}
                row[scope] = {"median": med, "rank": ranks(med, direction)}
            rows[key] = row
        out[qid] = {"title": title, "metrics": rows}
    return out


def analysis_lines(an, arms):
    lines = ["", "## Efficiency analysis", "",
             "Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric "
             "(1 is best, none for descriptive metrics).", ""]
    for qid, q in an.items():
        lines += [f"### {qid} {q['title']}", "", "| Metric | Scope | " + " | ".join(arms) + " |",
                  "|---|---|" + "---|" * len(arms)]
        for key, row in q["metrics"].items():
            for scope in ("all", *SIZES):
                cell = row[scope]
                if scope != "all" and all(v is None for v in cell["median"].values()):
                    continue
                vals = [fmt(cell["median"][a]) + (f" #{cell['rank'][a]}" if a in cell["rank"] else "")
                        for a in arms]
                lines.append(f"| {key} | {scope} | " + " | ".join(vals) + " |")
        lines.append("")
    return lines


RUN_COLUMNS = ("tokens_total", "tokens_per_task", "tasks_done", "tasks_planned", "wall_min",
               "main_min", "agent_min", "cold_starts", "error_rate", "plan_coverage", "accept")


def six_lines(data):
    """M1 to M6 per arm as totals and medians over its runs, then one row per run."""
    derived = {arm: [(sc, i + 1, six.derive(m)) for sc, runs in sorted(scs.items())
                     for i, m in enumerate(runs)] for arm, scs in sorted(data.items())}
    lines = ["## Six metrics", "",
             "Totals sum the runs of the arm (n/a for ratios); medians are over its runs.", ""]
    for arm, runs in derived.items():
        flat = [m for _, _, m in runs]
        lines += [f"### Arm {arm} ({len(flat)} runs)", "", "| Metric | Field | Total | Median |",
                  "|---|---|---|---|"]
        for mid, (title, fields) in six.METRICS.items():
            lines += [f"| {mid} {title} | {f} | {fmt(six.total(flat, f))} | {fmt(six.median(flat, f))} |"
                      for f in fields]
        lines.append("")
    lines += ["### Per run", "", "| Run | " + " | ".join(RUN_COLUMNS) + " |",
              "|---|" + "---|" * len(RUN_COLUMNS)]
    for arm, runs in derived.items():
        lines += [f"| {arm} {sc} r{n} | " + " | ".join(fmt(m.get(c)) for c in RUN_COLUMNS) + " |"
                  for sc, n, m in runs]
    return lines + [""]


def build(data, base=BASE, cand=CAND, reps=None, sizes=None):
    res = evaluate(data, base, cand)
    counts = run_counts(data, base, cand, reps)
    lines = ["# Evaluation report", "", f"Candidate {cand} versus base {base}.", ""]
    lines += six_lines(data)
    lines += ["## Runs", "", "| Arm and scenario | Found | Expected | Missing |",
             "|---|---|---|---|"]
    lines += [f"| {k} | {c['found']} | {c['expected']} | {c['missing']} |" for k, c in counts.items()]
    lines += ["", "## Hard gates", ""]
    lines += [f"- {'PASS' if g['ok'] else 'FAIL'}: {g['rule']} ({g['detail']})" for g in res["gates"]]
    for sc, row in res["scorecard"].items():
        lines += ["", f"## Scorecard {sc}", "", f"| Metric | Group | {cand} | {base} | Band | Verdict |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| {k} | {GROUP_LABELS.get(c['group'], c['group'])} | {fmt(c['lt'])} | {fmt(c['sk'])} | {fmt(c['band'])} | "
                  f"{c['verdict'] or 'n/a'} |" for k, c in row.items()]
    lines += ["", "## Tally", "", "| Group | Win | Tie | Loss |", "|---|---|---|---|"]
    lines += [f"| {GROUP_LABELS.get(g, g)} | {t['win']} | {t['tie']} | {t['loss']} |"
              for g, t in res["tally"].items()]
    lines += ["", "## Adoption", "",
              f"- {'PASS' if res['gates_ok'] else 'FAIL'}: hard gates",
              f"- {'PASS' if res['speed_ok'] else 'FAIL'}: E1, E2, E3 win or tie on S1 and S2 "
              f"({json.dumps(res['speed'])})",
              f"- {'PASS' if res['groups_ok'] else 'FAIL'}: losses do not exceed wins in each group",
              "", f"Result: {cand} is {'adopted' if res['adopt'] else 'not adopted'}.", ""]
    if res["work_list"]:
        lines += ["## Work list", ""]
        lines += [f"- {w['scenario']} {w['metric']} ({w['group']}): {cand} {fmt(w['lt'])}, {base} {fmt(w['sk'])}"
                  for w in res["work_list"]] + [""]
    missing = sum(c["missing"] for c in counts.values())
    if missing:
        lines += [f"{missing} run(s) are missing; medians use only the runs present.", ""]
    an = analyze(data, sizes)
    lines += analysis_lines(an, sorted(data))
    return "\n".join(lines), {"runs": counts, "medians": medians(data), "analysis": an, **res}


def scenario_sizes(config):
    """{scenario: size} from the expected.json files of the config's scenarios folder."""
    if not config:
        return {}
    cfg_path = Path(config)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    folder = cfg_path.resolve().parent / cfg.get("scenarios_dir", "scenarios")
    sizes = {}
    for sc in cfg.get("scenarios", {}):
        try:
            exp = json.loads((folder / sc / "expected.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(exp, dict) and exp.get("size"):
            sizes[sc] = exp["size"]
    return sizes


def write_report(results, base=BASE, cand=CAND, config=None):
    """config: path of the arms json whose scenarios give the expected reps; derived from the files when absent."""
    if config:
        reps = expected_reps(json.loads(Path(config).read_text(encoding="utf-8")))
    else:
        reps = derive_reps(results)
        if set(reps) <= set(EXPECTED_REPS):
            reps = None  # the small suite: its fixed map
    text, payload = build(load(results), base, cand, reps, scenario_sizes(config))
    out = Path(results) / ("report.md" if base == BASE else f"report-{cand}-vs-{base}.md")
    out.write_text(text, encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (Path(results) / "analysis.json").write_text(json.dumps(payload["analysis"], indent=2),
                                                 encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("base_arm", nargs="?", default=BASE)
    ap.add_argument("--config", help="arms json that gives the expected repetitions")
    a = ap.parse_args()
    print(write_report(a.results, a.base_arm, config=a.config))

"""Scorecard and adoption decision from `<arm>-<scenario>-r<n>.metrics.json` (decision rule of README)."""
import json
import re
import statistics
import sys
from pathlib import Path

CAND, BASE = "LT", "SK"
EXPECTED_REPS = {"S1": 2, "S2": 2, "S3": 1, "S4": 1}
NAME = re.compile(r"^(?P<arm>[^-]+)-(?P<sc>.+)-r(?P<n>\d+)$")
LOWER, HIGHER = "lower", "higher"
GROUPS = {
    "fidelity": {"plan_coverage": HIGHER, "plan_drift": LOWER, "traceability": HIGHER,
                 "docs_first": HIGHER, "promoted": HIGHER, "single_source": LOWER},
    "efficiency": {"tokens_total": LOWER, "cost_usd": LOWER, "wall_min": LOWER, "turns": LOWER,
                   "context_peak": LOWER, "min_to_code": LOWER, "doc_bytes": LOWER,
                   "cost_per_accept": LOWER},
    "errors": {"tool_errors": LOWER, "kit_self_fixes": LOWER, "rework_commits": LOWER},
}
GATE_ONLY = ["accept", "suite_green", "gate_ok", "completed", "prd_fidelity", "protocol_adherence"]
REPORT_ONLY = ["subagents", "subagent_token_share"]
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
        if isinstance(data, dict):
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


def gates(data):
    cand = [m for s in data.get(CAND, {}).values() for m in s]
    base = [m for s in data.get(BASE, {}).values() for m in s]
    out = []

    def add(rule, ok, detail):
        out.append({"rule": rule, "ok": bool(ok), "detail": detail})

    ca, ba = mean(values(cand, "accept")), mean(values(base, "accept"))
    add("Q1 accept: LT mean at least SK", ca is not None and (ba is None or ca >= ba),
        f"LT {ca}, SK {ba}")
    for key, label in (("suite_green", "Q2"), ("gate_ok", "Q3"), ("completed", "Q4")):
        ok = bool(cand) and all(m.get(key) is True for m in cand)
        add(f"{label} {key}: true in every LT run", ok,
            f"{sum(1 for m in cand if m.get(key) is True)} of {len(cand)}")
    cf, bf = mean(values(cand, "prd_fidelity")), mean(values(base, "prd_fidelity"))
    add("F1 prd_fidelity: LT at least SK minus 0.05",
        cf is not None and (bf is None or cf >= bf - F1_SLACK), f"LT {cf}, SK {bf}")
    add("R4 protocol_adherence: 1.0 in every LT run",
        bool(cand) and all(m.get("protocol_adherence") == 1.0 for m in cand),
        f"{sum(1 for m in cand if m.get('protocol_adherence') == 1.0)} of {len(cand)}")
    return out


def scorecard(data):
    cards = {}
    for sc in sorted(set(data.get(CAND, {})) | set(data.get(BASE, {}))):
        cr, br = data.get(CAND, {}).get(sc, []), data.get(BASE, {}).get(sc, [])
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


def evaluate(data):
    gate_list = gates(data)
    cards = scorecard(data)
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


def run_counts(data):
    counts = {}
    for arm in (BASE, CAND):
        for sc, want in EXPECTED_REPS.items():
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


def build(data):
    res = evaluate(data)
    counts = run_counts(data)
    lines = ["# Evaluation report", "", "## Runs", "", "| Arm and scenario | Found | Expected | Missing |",
             "|---|---|---|---|"]
    lines += [f"| {k} | {c['found']} | {c['expected']} | {c['missing']} |" for k, c in counts.items()]
    lines += ["", "## Hard gates", ""]
    lines += [f"- {'PASS' if g['ok'] else 'FAIL'}: {g['rule']} ({g['detail']})" for g in res["gates"]]
    for sc, row in res["scorecard"].items():
        lines += ["", f"## Scorecard {sc}", "", "| Metric | Group | LT | SK | Band | Verdict |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| {k} | {c['group']} | {fmt(c['lt'])} | {fmt(c['sk'])} | {fmt(c['band'])} | "
                  f"{c['verdict'] or 'n/a'} |" for k, c in row.items()]
    lines += ["", "## Tally", "", "| Group | Win | Tie | Loss |", "|---|---|---|---|"]
    lines += [f"| {g} | {t['win']} | {t['tie']} | {t['loss']} |" for g, t in res["tally"].items()]
    lines += ["", "## Adoption", "",
              f"- {'PASS' if res['gates_ok'] else 'FAIL'}: hard gates",
              f"- {'PASS' if res['speed_ok'] else 'FAIL'}: E1, E2, E3 win or tie on S1 and S2 "
              f"({json.dumps(res['speed'])})",
              f"- {'PASS' if res['groups_ok'] else 'FAIL'}: losses do not exceed wins in each group",
              "", f"Result: {'LT is adopted' if res['adopt'] else 'LT is not adopted'}.", ""]
    if res["work_list"]:
        lines += ["## Work list", ""]
        lines += [f"- {w['scenario']} {w['metric']} ({w['group']}): LT {fmt(w['lt'])}, SK {fmt(w['sk'])}"
                  for w in res["work_list"]] + [""]
    missing = sum(c["missing"] for c in counts.values())
    if missing:
        lines += [f"{missing} run(s) are missing; medians use only the runs present.", ""]
    return "\n".join(lines), {"runs": counts, "medians": medians(data), **res}


def write_report(results):
    text, payload = build(load(results))
    out = Path(results) / "report.md"
    out.write_text(text, encoding="utf-8")
    (Path(results) / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: report.py <results_dir>")
    print(write_report(sys.argv[1]))

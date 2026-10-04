"""Write report.md from the per-pair metrics files of one run (EV09, decision rule of README)."""
import json
import sys
from pathlib import Path

ROWS = ["status", "completed", "hidden_pass", "suite_green", "gate_ok", "prd_ok", "ids_in_tests",
        "docs_first", "planned_left", "dup_count", "fr_lines", "cost_usd", "duration_min",
        "turns", "tokens_total", "doc_bytes"]
SUMS = ["planned_left", "dup_count", "fr_lines", "cost_usd", "duration_min", "turns",
        "tokens_total", "doc_bytes"]
TOLERANCE = 1.10


def load(results):
    data = {}
    for f in sorted(Path(results).glob("*.metrics.json")):
        arm, _, rest = f.name[: -len(".metrics.json")].partition("-")
        data.setdefault(arm, {})[rest] = json.loads(f.read_text(encoding="utf-8"))
    return data


def num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0


def totals(runs):
    t = {k: sum(num(m.get(k)) for m in runs.values()) for k in SUMS}
    passed = sum(num(m.get("hidden_passed")) for m in runs.values())
    total = sum(num(m.get("hidden_total")) for m in runs.values())
    t["hidden_pass"] = passed / total if total else 0.0
    t["prd_ok"] = sum(1 for m in runs.values() if m.get("prd_ok"))
    t["gate_ok"] = sum(1 for m in runs.values() if m.get("gate_ok"))
    t["completed"] = sum(1 for m in runs.values() if m.get("completed"))
    t["runs"] = len(runs)
    return t


def evaluate(data):
    """Decision rule: list of (rule, passed, detail). Pure function over {arm: {scenario: metrics}}."""
    a, b = totals(data.get("A", {})), totals(data.get("B", {}))
    out = [
        ("hidden_pass of B is not lower than A", b["hidden_pass"] >= a["hidden_pass"],
         f"A {a['hidden_pass']:.3f}, B {b['hidden_pass']:.3f}"),
        ("prd_ok of B is not lower than A", b["prd_ok"] >= a["prd_ok"],
         f"A {a['prd_ok']:.0f}, B {b['prd_ok']:.0f}"),
        ("gate_ok holds in every B run", b["runs"] > 0 and b["gate_ok"] == b["runs"],
         f"{b['gate_ok']:.0f} of {b['runs']}"),
        ("dup_count of B is not higher than A", b["dup_count"] <= a["dup_count"],
         f"A {a['dup_count']:.0f}, B {b['dup_count']:.0f}"),
        ("cost_usd of B is at most 10% above A", b["cost_usd"] <= a["cost_usd"] * TOLERANCE,
         f"A {a['cost_usd']:.2f}, B {b['cost_usd']:.2f}"),
        ("duration_min of B is at most 10% above A",
         b["duration_min"] <= a["duration_min"] * TOLERANCE,
         f"A {a['duration_min']:.1f}, B {b['duration_min']:.1f}"),
    ]
    return out


def close_scenarios(data):
    """Scenarios whose cost or duration differs by 10% or less in either direction: rerun them."""
    close = []
    for sc in sorted(set(data.get("A", {})) & set(data.get("B", {}))):
        for key in ("cost_usd", "duration_min"):
            x, y = num(data["A"][sc].get(key)), num(data["B"][sc].get(key))
            if x and abs(y - x) <= 0.10 * x:
                close.append(f"{sc} ({key})")
    return close


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    return str(v)


def delta(x, y):
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (x, y)):
        return fmt(round(y - x, 4))
    return ""


def table(title, rows):
    lines = [f"## {title}", "", "| Metric | A | B | Delta |", "|---|---|---|---|"]
    lines += [f"| {k} | {fmt(x)} | {fmt(y)} | {delta(x, y)} |" for k, x, y in rows]
    return lines + [""]


def build(data):
    lines = ["# Evaluation report", ""]
    scenarios = sorted(set(data.get("A", {})) | set(data.get("B", {})))
    for sc in scenarios:
        ma, mb = data.get("A", {}).get(sc, {}), data.get("B", {}).get(sc, {})
        lines += table(f"Scenario {sc}", [(k, ma.get(k), mb.get(k)) for k in ROWS])
    a, b = totals(data.get("A", {})), totals(data.get("B", {}))
    keys = ["runs", "completed", "hidden_pass", "prd_ok", "gate_ok", *SUMS]
    lines += table("Totals", [(k, a[k], b[k]) for k in keys])
    lines += ["## Decision rule", ""]
    results = evaluate(data)
    lines += [f"- {'PASS' if ok else 'FAIL'}: {rule} ({detail})" for rule, ok, detail in results]
    adopt = all(ok for _, ok, _ in results)
    lines += ["", f"Result: {'B is adopted' if adopt else 'B is not adopted'} on this run.", ""]
    close = close_scenarios(data)
    if close:
        lines += ["Within 10% of each other, rerun before deciding: " + ", ".join(close) + ".", ""]
    lines += ["Caveat: one repetition per pair gives the direction only, not a verdict.", ""]
    return "\n".join(lines)


def write_report(results):
    out = Path(results) / "report.md"
    out.write_text(build(load(results)), encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: report.py <results_dir>")
    print(write_report(sys.argv[1]))

"""Adoption verdict of MAINTAINING.md M07: a candidate column against the baseline column."""
import six

BAND = 0.10
DECIDING = "S5"
MAX_TOKENS_MAIN = 3_500_000


def stats(runs, field):
    """(mean, spread) of a field over the reps of one scenario; None when no rep has it."""
    v = six.vals(runs, field)
    return (sum(v) / len(v), max(v) - min(v)) if v else None


def outcome(field, base, cand):
    """'win', 'tie' or 'loss' of cand against base, or None without a direction or a value.
    The noise band is the spread of the reps; one rep on either side has no spread, so the 10% floor applies."""
    direction = six.DIRECTION.get(field)
    if direction is None or base is None or cand is None:
        return None
    band = max(base[1], cand[1])
    if band == 0:
        band = BAND * abs(base[0])
    delta = cand[0] - base[0]
    if abs(delta) <= band:
        return "tie"
    return "win" if (delta > 0) == (direction == six.HIGHER) else "loss"


def tally(base_runs, cand_runs):
    """{metric id: {win, tie, loss}} over every directed field and every scenario both columns ran."""
    out = {}
    for mid, (_, fields) in six.METRICS.items():
        t = out[mid] = {"win": 0, "tie": 0, "loss": 0}
        for f in dict.fromkeys(fields):
            for sc in sorted(set(base_runs) & set(cand_runs)):
                o = outcome(f, stats(base_runs[sc], f), stats(cand_runs[sc], f))
                if o:
                    t[o] += 1
    return out


def _median_within(base_runs, cand_runs, field):
    b = six.median(base_runs.get(DECIDING, []), field)
    c = six.median(cand_runs.get(DECIDING, []), field)
    if b is None or c is None:
        return None, "no data"
    ok = c <= b * (1 + BAND)
    return ok, f"{c:.3f} vs {b:.3f}" + (f" ({c / b - 1:+.0%})" if b else "")


def _all(cand_runs, field, ok):
    """(ok or None, detail) of a hard gate over every candidate run that has the field."""
    v = [x for runs in cand_runs.values() for x in six.vals(runs, field)]
    if not v:
        return None, "no data"
    bad = sum(1 for x in v if not ok(x))
    return bad == 0, f"{bad} of {len(v)} runs fail"


def hard_gates(cand_runs):
    """[(label, ok or None, detail)] of the hard gates of eval/METRICS.md, judged on the candidate alone."""
    gates = []
    runs = [r for rs in cand_runs.values() for r in rs]
    has = [r for r in runs if six.vals([r], "hidden_passed") and six.vals([r], "hidden_total")]
    missing = len(runs) - len(has)
    bad = sum(1 for r in has if r["hidden_passed"] != r["hidden_total"])
    gates.append(("Behavior: hidden tests 100% (hard gate)", (bad + missing == 0) if runs else None,
                  f"{bad} of {len(has)} runs fail, {missing} had no hidden result"))
    for label, field, test in (("Consistent PRD: contradiction_left 0", "contradiction_left", lambda x: x == 0),
                               ("Conflict recall 1.0", "conflict_recall", lambda x: x == 1.0),
                               ("Protocol: dispatch_map 1.0", "dispatch_map", lambda x: x == 1.0),
                               ("Protocol: review_coverage 1.0", "review_coverage", lambda x: x == 1.0),
                               ("Protocol: main_violations 0", "main_violations", lambda x: x == 0),
                               ("Protocol: chief_violations 0", "chief_violations", lambda x: x == 0),
                               ("Protocol: return_compliance 1.0", "return_compliance", lambda x: x == 1.0),
                               ("Protocol: closed true", "closed", lambda x: x == 1.0)):
        ok, detail = _all(cand_runs, field, test)
        gates.append((f"{label} (hard gate)", ok, detail))
    first = [r["surveyor_first"] for r in runs if isinstance(r.get("surveyor_first"), bool)]
    gates.append(("Protocol: surveyor_first true (hard gate)", all(first) if first else None,
                  f"{first.count(False)} of {len(first)} runs fail" if first else "no data"))
    return gates


def rules(base_runs, cand_runs):
    """[(label, ok or None, detail)]; ok None means no data to decide."""
    t = tally(base_runs, cand_runs)
    out = hard_gates(cand_runs)
    for f in ("cost_per_accept", "runner_wall_min"):
        ok, detail = _median_within(base_runs, cand_runs, f)
        out.append((f"{DECIDING} {f} median within +{BAND:.0%}", ok, detail))
    peaks = [v for runs in cand_runs.values() for v in six.vals(runs, "tokens_main")]
    out.append((f"tokens_main per run at most {MAX_TOKENS_MAIN / 1e6:.1f}M",
                max(peaks) <= MAX_TOKENS_MAIN if peaks else None,
                f"max {max(peaks):.0f}" if peaks else "no data"))
    for mid, (title, _) in six.METRICS.items():
        c = t[mid]
        n = c["win"] + c["tie"] + c["loss"]
        out.append((f"{mid} {title}: wins at least losses", c["win"] >= c["loss"] if n else None,
                    f"{c['win']} win / {c['tie']} tie / {c['loss']} loss"))
    return out


def render(base_label, cols):
    """Markdown 'Adoption (M07)' section and the overall verdicts by candidate label."""
    base = dict(cols).get(base_label)
    lines = ["## Adoption (M07)", ""]
    if base is None:
        return "\n".join(lines + [f"Baseline {base_label} not found among the columns.", ""]), {}
    overall = {}
    for label, runs in cols:
        if label == base_label:
            continue
        results = rules(base, runs)
        overall[label] = all(ok is not False for _, ok, _ in results)
        lines += [f"### {label} against {base_label}", ""]
        for name, ok, detail in results:
            lines.append(f"- {'N/A ' if ok is None else 'PASS' if ok else 'FAIL'} {name}: {detail}")
        lines += ["", f"Verdict {label}: {'PASS' if overall[label] else 'FAIL'}", ""]
    return "\n".join(lines), overall

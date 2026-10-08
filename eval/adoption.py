"""Adoption verdict of MAINTAINING.md M07: a candidate column against the baseline column."""
import six

BAND = 0.10
DECIDING = "S5"
MAX_TOKENS_MAIN = 3_500_000
HARD = ("M2", "M7", "M8")


def stats(runs, field):
    """(mean, spread) of a field over the reps of one scenario; None when no rep has it."""
    v = six.vals(runs, field)
    return (sum(v) / len(v), max(v) - min(v)) if v else None


def outcome(field, base, cand):
    """'win', 'tie' or 'loss' of cand against base, or None without a direction or a value."""
    direction = six.DIRECTION.get(field)
    if direction is None or base is None or cand is None:
        return None
    band = max(BAND * abs(base[0]), base[1], cand[1])
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


def _within(base_runs, cand_runs, field):
    b, c = stats(base_runs.get(DECIDING, []), field), stats(cand_runs.get(DECIDING, []), field)
    if b is None or c is None:
        return None, "no data"
    ratio = c[0] / b[0] if b[0] else None
    ok = c[0] <= b[0] * (1 + BAND)
    return ok, f"{c[0]:.3f} vs {b[0]:.3f}" + (f" ({ratio - 1:+.0%})" if ratio else "")


def rules(base_runs, cand_runs):
    """[(label, ok or None, detail)]; ok None means no data to decide."""
    t = tally(base_runs, cand_runs)
    out = []
    for mid in HARD:
        n = t[mid]["win"] + t[mid]["tie"] + t[mid]["loss"]
        out.append((f"{mid} not worse (hard gate)", t[mid]["loss"] == 0 if n else None,
                    f"{t[mid]['loss']} losses over {n} comparisons"))
    for f in ("cost_usd", "wall_min"):
        ok, detail = _within(base_runs, cand_runs, f)
        out.append((f"{DECIDING} {f} within +{BAND:.0%}", ok, detail))
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

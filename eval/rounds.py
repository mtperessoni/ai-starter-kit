"""Compare rounds: recompute the eight metrics offline from result folders (no claude calls, no judge).

Usage: python eval/rounds.py <results-folder>[:<arm>] ... [--baseline folder:ARM] [--out file.md]
"""
import argparse
import json
from pathlib import Path

import adoption
import report
import six
import transcript


def parse_spec(spec):
    path, sep, arm = spec.rpartition(":")
    if not sep or "/" in arm or "\\" in arm or not arm:
        return spec, None
    return path, arm


def load_column(folder, arm):
    """{scenario: [six-metric run dict]} for one arm of one results folder."""
    runs = {}
    for stem, metrics in sorted(_metrics(folder, arm)):
        summary = None
        log = Path(folder) / f"{stem}.jsonl"
        if log.is_file():
            logs = [log] + sorted(Path(folder).glob(f"{stem}.p[2-9].jsonl"))
            summary = transcript.summarize_phases(logs)
        sc = report.NAME.match(stem)["sc"]
        runs.setdefault(sc, []).append(six.derive(metrics, summary))
    return runs


def _metrics(folder, arm):
    for f in sorted(Path(folder).glob("*.metrics.json")):
        stem = f.name[: -len(".metrics.json")]
        m = report.NAME.match(stem)
        if not m or (arm and m["arm"] != arm):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("status") not in report.INFRA:
            yield stem, data


def _arms(folder):
    return sorted({m["arm"] for f in Path(folder).glob("*.metrics.json")
                   if (m := report.NAME.match(f.name[: -len(".metrics.json")]))})


def columns(specs):
    """[(label, {scenario: runs})] with one entry per folder and arm."""
    cols = []
    for spec in specs:
        path, arm = parse_spec(spec)
        for a in ([arm] if arm else _arms(path)):
            cols.append((f"{Path(path).name}:{a}", load_column(path, a)))
    return cols


def _cell(runs, field):
    """Mean over the reps of one scenario, with the spread (max minus min) when there are several."""
    st = adoption.stats(runs, field) if runs else None
    if st is None:
        return "n/a"
    reps = len(six.vals(runs, field))
    return report.fmt(st[0]) + (f" (spread {report.fmt(st[1])})" if reps > 1 else "")


def render(specs, baseline=None):
    cols = columns(specs)
    scenarios = sorted({sc for _, runs in cols for sc in runs})
    lines = ["# Metrics M1 to M8 by round", ""]
    for mid, (title, fields) in six.METRICS.items():
        lines += [f"## {mid} {title}", "", "| Row | " + " | ".join(c[0] for c in cols) + " |",
                  "|---|" + "---|" * len(cols)]
        for f in fields:
            for sc in scenarios:
                lines.append(f"| {f} {sc} | " + " | ".join(_cell(r.get(sc), f) for _, r in cols) + " |")
            label = "total" if f in six.ADDITIVE else "median"
            allruns = [[m for ms in r.values() for m in ms] for _, r in cols]
            fn = six.total if f in six.ADDITIVE else six.median
            lines.append(f"| {f} {label} | " + " | ".join(report.fmt(fn(x, f)) for x in allruns) + " |")
        lines.append("")
    if baseline:
        path, arm = parse_spec(baseline)
        lines.append(adoption.render(f"{Path(path).name}:{arm}", cols)[0])
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folders", nargs="+", help="results-folder or results-folder:ARM")
    ap.add_argument("--baseline", help="results-folder:ARM column the others are judged against")
    ap.add_argument("--out", help="also write the tables to this markdown file")
    a = ap.parse_args(argv)
    text = render(a.folders, a.baseline)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

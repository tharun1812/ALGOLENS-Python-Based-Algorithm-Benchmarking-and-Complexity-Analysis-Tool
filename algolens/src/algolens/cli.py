"""Command line interface: `python -m algolens --help`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence, TextIO

from . import __version__
from .experiment import (classify_searching, classify_sorting, run_searching, run_sorting, write_csv, write_json)
from .generators import DISTRIBUTIONS, make_input
from .instrument import wrap
from .searching import SEARCHES
from .sorting import SORTS

MARK = {True: "yes", False: "NO", None: "-"}


def _table(rows: list[dict], headers: list[str], out: TextIO) -> None:
    widths = [max(len(h), *(len(str(r.get(h, ""))) for r in rows)) for h in headers]
    print("  ".join(h.upper().ljust(w) for h, w in zip(headers, widths)), file=out)
    print("  ".join("-" * w for w in widths), file=out)
    for r in rows:
        print("  ".join(str(r.get(h, "")).ljust(w) for h, w in zip(headers, widths)), file=out)


def report_markdown(title: str, rows: list[dict], headers: list[str]) -> str:
    lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        cells = [(MARK[r[h]] if h == "match" else str(r.get(h, ""))) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def cmd_list(args, out: TextIO) -> int:
    print("sorting:   " + ", ".join(f"{s.name} ({s.kind})" for s in SORTS.values()), file=out)
    print("searching: " + ", ".join(SEARCHES), file=out)
    print("inputs:    " + ", ".join(DISTRIBUTIONS), file=out)
    return 0


def cmd_verify(args, out: TextIO) -> int:
    """Check every algorithm against Python's own sort and bisect on assorted inputs."""
    failures = 0
    for name, spec in SORTS.items():
        for dist in DISTRIBUTIONS:
            for n in (0, 1, 2, 3, 10, 257):
                values = make_input(dist, n, seed=5) if n else []
                arr = wrap(values)
                spec.fn(arr)
                if arr.values != sorted(values):
                    failures += 1
                    print(f"FAIL sort {name} on {dist} n={n}", file=out)
    for name, spec in SEARCHES.items():
        for n in (1, 2, 17, 500):
            values = sorted(set(make_input("random", n, seed=5)))
            for target in [*values, -1, max(values) + 1, values[0] + 1]:
                arr = wrap(values)
                probe = wrap([target], arr.stats)[0]
                found = spec.fn(arr, probe)
                expected = values.index(target) if target in values else -1
                if found != expected:
                    failures += 1
                    print(f"FAIL search {name} n={len(values)} target={target}", file=out)
    print("all algorithms verified" if not failures else f"{failures} failure(s)", file=out)
    return 1 if failures else 0


def cmd_analyze(args, out: TextIO) -> int:
    from . import plots
    folder = Path(args.out)
    log = (lambda msg: print(f"  measuring {msg}", file=out)) if args.verbose else None
    max_n = 1024 if args.quick else None
    if args.kind == "sort":
        records = run_sorting(args.algorithms or None, args.inputs or DISTRIBUTIONS, trials=2 if args.quick else 3, seed=args.seed, max_n=max_n, progress=log)
        rows = classify_sorting(records)
        write_csv(folder / "sorting_measurements.csv", records)
        write_csv(folder / "sorting_classification.csv", rows)
        headers = ["algorithm", "distribution", "metric", "measured", "exponent", "textbook", "match"]
        (folder / "sorting_report.md").write_text(report_markdown("Sorting: inferred complexity vs textbook", rows, headers), encoding="utf-8")
        dists = {r["distribution"] for r in records}
        if "random" in dists:
            plots.plot_growth(records, "random", folder / "growth_random.png")
        plots.plot_input_sensitivity(records, folder / "input_sensitivity.png")
        plots.plot_fingerprint(rows, folder / "fingerprint.png")
        _table(rows, headers, out)
        checked = [r for r in rows if r["match"] is not None]
        print(f"\n{sum(r['match'] for r in checked)} of {len(checked)} classes with a textbook answer matched", file=out)
    else:
        records = run_searching(args.algorithms or None, seed=args.seed, max_n=max_n, progress=log)
        rows = classify_searching(records)
        write_csv(folder / "search_measurements.csv", records)
        write_csv(folder / "search_classification.csv", rows)
        headers = ["algorithm", "measured", "exponent", "textbook", "match", "comparisons_at_largest_n", "largest_n"]
        (folder / "search_report.md").write_text(report_markdown("Searching: inferred complexity vs textbook", rows, headers), encoding="utf-8")
        plots.plot_search(records, folder / "search_growth.png")
        _table(rows, headers, out)
    write_json(folder / f"{args.kind}_results.json", {"classification": rows})
    print(f"\nwrote results to {folder}/", file=out)
    return 0


def cmd_animate(args, out: TextIO) -> int:
    from .animate import make_gif
    path = make_gif(args.algorithm, args.out or f"{args.algorithm}.gif", n=args.n, distribution=args.input, seed=args.seed)
    print(f"wrote {path}", file=out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="algolens", description="Measure algorithms and infer their complexity from the data.")
    p.add_argument("--version", action="version", version=f"algolens {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="show the available algorithms and input types").set_defaults(func=cmd_list)
    sub.add_parser("verify", help="check every algorithm for correctness").set_defaults(func=cmd_verify)

    a = sub.add_parser("analyze", help="run the experiments, infer complexity, write tables and charts")
    a.add_argument("kind", choices=["sort", "search"])
    a.add_argument("--algorithms", nargs="+", help="subset of algorithms (default: all)")
    a.add_argument("--inputs", nargs="+", choices=DISTRIBUTIONS, help="sorting input types (default: all)")
    a.add_argument("--out", default="results")
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--quick", action="store_true", help="smaller sizes and fewer trials (seconds instead of minutes)")
    a.add_argument("--verbose", action="store_true")
    a.set_defaults(func=cmd_analyze)

    g = sub.add_parser("animate", help="write an animated GIF of a sorting algorithm")
    g.add_argument("algorithm", choices=list(SORTS))
    g.add_argument("--n", type=int, default=36)
    g.add_argument("--input", choices=DISTRIBUTIONS, default="random")
    g.add_argument("--seed", type=int, default=3)
    g.add_argument("--out")
    g.set_defaults(func=cmd_animate)
    return p


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, out or sys.stdout)
    except (ValueError, AssertionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

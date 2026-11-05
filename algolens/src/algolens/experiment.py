"""Run the experiments: measure operation counts over growing input sizes, then classify the growth."""
from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from .complexity import SEARCH_MODELS, SORT_MODELS, fit_complexity
from .generators import DISTRIBUTIONS, make_input, make_sorted_unique
from .instrument import Stats, wrap
from .searching import SEARCHES
from .sorting import SORTS
from .theory import SEARCH_THEORY, SORT_THEORY, SORT_WRITE_THEORY

DETERMINISTIC = {"sorted", "reversed"}          # no randomness, so one trial is enough


def sizes_for(max_n: int, start: int = 64) -> list[int]:
    out, n = [], start
    while n <= max_n:
        out.append(n)
        n *= 2
    return out


def run_sorting(algorithms: Iterable[str] | None = None, distributions: Iterable[str] = DISTRIBUTIONS, trials: int = 3,
                seed: int = 0, max_n: int | None = None, progress: Callable[[str], None] | None = None) -> list[dict]:
    """Measure comparisons, writes and wall time. Every run is verified to have produced a correctly sorted result."""
    records: list[dict] = []
    for name in (algorithms or SORTS):
        spec = SORTS[name]
        for dist in distributions:
            if progress:
                progress(f"{name} / {dist}")
            for n in sizes_for(min(spec.max_n, max_n or spec.max_n)):
                for trial in range(1 if dist in DETERMINISTIC else trials):
                    values = make_input(dist, n, seed, trial)
                    arr = wrap(values, Stats())
                    t0 = time.perf_counter()
                    spec.fn(arr)
                    seconds = time.perf_counter() - t0
                    if arr.values != sorted(values):
                        raise AssertionError(f"{name} produced a wrong result on {dist} input of size {n}")
                    records.append({"algorithm": name, "distribution": dist, "n": n, "trial": trial,
                                    "comparisons": arr.stats.comparisons, "writes": arr.stats.writes, "seconds": round(seconds, 6)})
    return records


def run_searching(algorithms: Iterable[str] | None = None, queries: int = 200, seed: int = 0, max_n: int | None = None,
                  progress: Callable[[str], None] | None = None) -> list[dict]:
    """Average comparisons per query on evenly spread sorted data; half the queries are present, half absent."""
    records: list[dict] = []
    for name in (algorithms or SEARCHES):
        spec = SEARCHES[name]
        if progress:
            progress(name)
        for n in sizes_for(min(spec.max_n, max_n or spec.max_n), start=256):
            values = make_sorted_unique(n, seed)
            rng = np.random.default_rng([seed, n, 7])
            present = [values[i] for i in rng.integers(0, n, queries // 2)]
            absent = [v + 1 for v in present if (v + 1) not in set(values)] or [-1] * (queries // 2)
            targets = present + absent
            members = set(values)
            arr = wrap(values, Stats())                  # built once per size; only the counters are reset per query
            total = 0
            for t in targets:
                probe = wrap([t], arr.stats)[0]
                arr.stats.reset()
                found = spec.fn(arr, probe)
                if (found != -1) != (t in members) or (found != -1 and arr[found].value != t):
                    raise AssertionError(f"{name} gave a wrong answer searching {t} in a list of {n}")
                total += arr.stats.comparisons
            records.append({"algorithm": name, "n": n, "queries": len(targets), "comparisons_per_query": total / len(targets)})
    return records


def _series(records: list[dict], keys: tuple[str, ...], value: str) -> dict[tuple, tuple[list[int], list[float]]]:
    grouped: dict[tuple, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        grouped[tuple(r[k] for k in keys)][r["n"]].append(r[value])
    return {key: (sorted(by_n), [float(np.mean(by_n[n])) for n in sorted(by_n)]) for key, by_n in grouped.items()}


def classify_sorting(records: list[dict]) -> list[dict]:
    """One row per (algorithm, distribution). Comparison sorts are judged by comparisons, the others by array writes."""
    rows = []
    for (algo, dist), (ns, ys) in _series(records, ("algorithm", "distribution"), "comparisons").items():
        spec = SORTS[algo]
        metric = "comparisons" if spec.kind == "comparison" else "writes"
        if metric == "writes":
            ns, ys = _series(records, ("algorithm", "distribution"), "writes")[(algo, dist)]
        fit = fit_complexity(ns, ys, SORT_MODELS)
        expected = SORT_THEORY.get((algo, dist)) if metric == "comparisons" else SORT_WRITE_THEORY.get((algo, dist))
        rows.append({"algorithm": algo, "distribution": dist, "metric": metric, "measured": fit.best,
                     "exponent": round(fit.exponent, 2) if fit.exponent is not None else None,
                     "r2": round(fit.r2, 4) if fit.r2 is not None else None,
                     "textbook": expected or "",
                     "match": (fit.best == expected) if expected else None})
    return sorted(rows, key=lambda r: (list(SORTS).index(r["algorithm"]), list(DISTRIBUTIONS).index(r["distribution"])))


def classify_searching(records: list[dict]) -> list[dict]:
    rows = []
    for (algo,), (ns, ys) in _series(records, ("algorithm",), "comparisons_per_query").items():
        fit = fit_complexity(ns, ys, SEARCH_MODELS)
        expected = SEARCH_THEORY[algo]
        rows.append({"algorithm": algo, "measured": fit.best, "exponent": round(fit.exponent, 3), "r2": round(fit.r2, 4),
                     "textbook": expected, "match": fit.best == expected,
                     "comparisons_at_largest_n": round(ys[-1], 1), "largest_n": ns[-1]})
    return sorted(rows, key=lambda r: list(SEARCHES).index(r["algorithm"]))


def write_csv(path: str | Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str | Path, data: object) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

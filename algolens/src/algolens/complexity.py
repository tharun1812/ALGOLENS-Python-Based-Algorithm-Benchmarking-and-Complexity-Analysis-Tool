"""Infer a complexity class from measurements.

Idea: if y(n) really grows like c * f(n), then log(y / f(n)) is the same constant for every n. So for each candidate
f we compute how much log(y / f(n)) varies across the measured sizes (its standard deviation). The candidate with the
smallest variation fits best. When several candidates fit about equally well, the slowest-growing one wins, which is the
conservative, Occam's-razor choice. We also report the empirical exponent: the slope of log y against log n.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class Model:
    name: str
    f: Callable[[np.ndarray], np.ndarray]


SORT_MODELS: list[Model] = [          # ordered from slowest to fastest growth
    Model("O(1)", lambda n: np.ones_like(n, dtype=float)),
    Model("O(log n)", lambda n: np.log2(n)),
    Model("O(n)", lambda n: n.astype(float)),
    Model("O(n log n)", lambda n: n * np.log2(n)),
    Model("O(n^1.5)", lambda n: n ** 1.5),
    Model("O(n^2)", lambda n: n.astype(float) ** 2),
    Model("O(n^3)", lambda n: n.astype(float) ** 3),
]

SEARCH_MODELS: list[Model] = [
    Model("O(1)", lambda n: np.ones_like(n, dtype=float)),
    Model("O(log log n)", lambda n: np.log2(np.log2(n))),
    Model("O(log n)", lambda n: np.log2(n)),
    Model("O(sqrt n)", lambda n: np.sqrt(n)),
    Model("O(n)", lambda n: n.astype(float)),
]


@dataclass
class Fit:
    best: str
    exponent: float | None          # slope of log y vs log n
    r2: float | None                # how straight that log-log line is
    coefficient: float | None       # the c in y ~ c * f(n) for the chosen model
    scores: dict[str, float] = field(default_factory=dict)      # std of log(y / f(n)); lower is better


def fit_complexity(ns: Sequence[float], ys: Sequence[float], models: list[Model], tolerance: float = 0.03) -> Fit:
    n = np.asarray(ns, dtype=float)
    y = np.asarray(ys, dtype=float)
    if len(n) != len(y) or len(n) < 3:
        raise ValueError("need at least three (n, y) points of equal length")
    if np.all(y <= 0):
        return Fit("none", None, None, None)
    keep = (y > 0) & (n >= 4)
    n, y = n[keep], y[keep]
    if len(n) < 3:
        raise ValueError("need at least three positive measurements with n >= 4")

    scores: dict[str, float] = {}
    coefficients: dict[str, float] = {}
    for m in models:
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.log(y / m.f(n))
        if not np.all(np.isfinite(ratio)):
            continue
        scores[m.name] = float(np.std(ratio))
        coefficients[m.name] = float(np.exp(np.mean(ratio)))
    best_score = min(scores.values())
    best = next(m.name for m in models if m.name in scores and scores[m.name] <= best_score + tolerance)

    log_n, log_y = np.log(n), np.log(y)
    slope, intercept = np.polyfit(log_n, log_y, 1)
    predicted = slope * log_n + intercept
    ss_res, ss_tot = float(np.sum((log_y - predicted) ** 2)), float(np.sum((log_y - np.mean(log_y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return Fit(best, float(slope), r2, coefficients[best], scores)


def growth_rank(name: str, models: list[Model]) -> int:
    return [m.name for m in models].index(name)


def doubling_ratio(ns: Sequence[float], ys: Sequence[float]) -> float:
    """Average factor by which y grows each time n doubles (2 means linear, 4 quadratic, ~2.1 for n log n)."""
    n, y = np.asarray(ns, dtype=float), np.asarray(ys, dtype=float)
    ratios = [y[i + 1] / y[i] for i in range(len(y) - 1) if y[i] > 0 and abs(n[i + 1] / n[i] - 2) < 1e-9]
    return float(np.exp(np.mean(np.log(ratios)))) if ratios else math.nan

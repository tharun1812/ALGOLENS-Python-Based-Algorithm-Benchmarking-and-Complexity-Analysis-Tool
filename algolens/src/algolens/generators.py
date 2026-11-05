"""Input generators. Every one is deterministic for a given (seed, n, trial), so experiments are reproducible."""
from __future__ import annotations

import numpy as np

DISTRIBUTIONS = ("random", "sorted", "reversed", "nearly_sorted", "few_unique")


def rng_for(seed: int, n: int, trial: int) -> np.random.Generator:
    return np.random.default_rng([seed, n, trial])


def make_input(distribution: str, n: int, seed: int = 0, trial: int = 0) -> list[int]:
    rng = rng_for(seed, n, trial)
    if distribution == "random":
        return rng.integers(0, 4 * n, n).tolist()
    if distribution == "sorted":
        return sorted(rng.integers(0, 4 * n, n).tolist())
    if distribution == "reversed":
        return sorted(rng.integers(0, 4 * n, n).tolist(), reverse=True)
    if distribution == "nearly_sorted":
        data = sorted(rng.integers(0, 4 * n, n).tolist())
        for _ in range(max(1, n // 20)):               # swap about 5% of the positions, anywhere in the array
            i, j = rng.integers(0, n, 2)
            data[i], data[j] = data[j], data[i]
        return data
    if distribution == "few_unique":
        return rng.integers(0, 8, n).tolist()
    raise ValueError(f"unknown distribution '{distribution}', choose from {', '.join(DISTRIBUTIONS)}")


def make_sorted_unique(n: int, seed: int = 0) -> list[int]:
    """Evenly spread distinct values (the case interpolation search is designed for)."""
    rng = rng_for(seed, n, 99)
    return sorted(rng.choice(10 * n, size=n, replace=False).tolist())

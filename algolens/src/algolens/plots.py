"""Charts. All figures use a headless backend so they can be generated on any machine or in CI."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
import numpy as np                                    # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .experiment import _series                       # noqa: E402
from .generators import DISTRIBUTIONS                 # noqa: E402
from .sorting import SORTS                            # noqa: E402

PALETTE = ["#0f766e", "#d97706", "#1d4ed8", "#be123c", "#7c3aed", "#475569", "#0891b2", "#65a30d", "#c026d3"]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 100, "savefig.bbox": "tight"})


def _save(fig, path: str | Path) -> Path:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return Path(path)


def plot_growth(records: list[dict], distribution: str, path: str | Path) -> Path:
    """Comparisons against input size on log-log axes, with n, n log n and n^2 guide lines."""
    series = _series([r for r in records if r["distribution"] == distribution], ("algorithm",), "comparisons")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colour = {}
    for i, (key, (ns, ys)) in enumerate(sorted(series.items(), key=lambda kv: kv[1][1][-1])):
        if max(ys) == 0:
            continue
        colour[key[0]] = PALETTE[i % len(PALETTE)]
        ax.plot(ns, ys, marker="o", ms=4, lw=2, color=colour[key[0]], label=key[0])
    ns_all = np.array(sorted({n for ns, _ in series.values() for n in ns}), dtype=float)
    for label, f in [("n", ns_all), ("n log n", ns_all * np.log2(ns_all)), ("n²", ns_all ** 2)]:
        ax.plot(ns_all, f * 0.5 * (series[next(iter(series))][1][0] / f[0]), ls="--", lw=1, color="#94a3b8")
        ax.annotate(label, (ns_all[-1], f[-1] * 0.5 * (series[next(iter(series))][1][0] / f[0])), color="#64748b", fontsize=9, va="bottom")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("input size n")
    ax.set_ylabel("comparisons (mean)")
    ax.set_title(f"Comparisons vs input size: {distribution.replace('_', ' ')} input")
    ax.legend(ncol=2, fontsize=8, frameon=False)
    return _save(fig, path)


def plot_input_sensitivity(records: list[dict], path: str | Path,
                           algorithms=("insertion", "quick_naive", "quick_median3", "timsort")) -> Path:
    """One panel per algorithm: how the growth curve changes with the kind of input."""
    measured = list(dict.fromkeys(r["algorithm"] for r in records))
    algorithms = [a for a in algorithms if a in measured] or measured[:4]        # fall back when a subset was analysed
    fig, axes = plt.subplots(1, len(algorithms), figsize=(4 * len(algorithms), 3.8), sharey=False)
    axes = np.atleast_1d(axes)
    for ax, algo in zip(axes, algorithms):
        series = _series([r for r in records if r["algorithm"] == algo], ("distribution",), "comparisons")
        for i, dist in enumerate(DISTRIBUTIONS):
            if (dist,) in series:
                ns, ys = series[(dist,)]
                ax.plot(ns, ys, marker="o", ms=3, lw=1.8, color=PALETTE[i], label=dist.replace("_", " "))
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_title(algo)
        ax.set_xlabel("n")
    axes[0].set_ylabel("comparisons")
    axes[-1].legend(fontsize=8, frameon=False, loc="lower right")
    fig.suptitle("Same algorithm, different input: the growth curve changes", y=1.02)
    return _save(fig, path)


def plot_fingerprint(classification: list[dict], path: str | Path) -> Path:
    """Heatmap of the empirical exponent for every algorithm and input type, labelled with the inferred class."""
    algos = [a for a in SORTS if any(r["algorithm"] == a for r in classification)]
    dists = [d for d in DISTRIBUTIONS if any(r["distribution"] == d for r in classification)]
    grid = np.full((len(algos), len(dists)), np.nan)
    label = [["" for _ in dists] for _ in algos]
    for r in classification:
        i, j = algos.index(r["algorithm"]), dists.index(r["distribution"])
        if r["exponent"] is not None:
            grid[i, j] = r["exponent"]
            label[i][j] = r["measured"].replace("O(", "").rstrip(")").replace("n^2", "n²").replace("n^3", "n³") + ("*" if r["metric"] == "writes" else "")
    cmap = LinearSegmentedColormap.from_list("exp", ["#ccfbf1", "#fde68a", "#fb923c", "#b91c1c"])
    fig, ax = plt.subplots(figsize=(1.6 * len(dists) + 2, 0.5 * len(algos) + 2))
    im = ax.imshow(grid, cmap=cmap, vmin=1.0, vmax=2.1, aspect="auto")
    ax.set_xticks(range(len(dists)), [d.replace("_", " ") for d in dists])
    ax.set_yticks(range(len(algos)), algos)
    ax.grid(False)
    for i in range(len(algos)):
        for j in range(len(dists)):
            if label[i][j]:
                ax.text(j, i, f"{label[i][j]}\n{grid[i, j]:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if grid[i, j] > 1.8 else "#0f172a")
    ax.set_title("Complexity fingerprint: inferred class and empirical exponent")
    fig.colorbar(im, ax=ax, label="empirical exponent (slope of log-log fit)", shrink=0.8)
    fig.text(0.01, -0.02, "* judged by array writes (non-comparison sort); every other cell by comparisons", fontsize=8, color="#475569")
    return _save(fig, path)


def plot_search(records: list[dict], path: str | Path) -> Path:
    series = _series(records, ("algorithm",), "comparisons_per_query")
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for i, (key, (ns, ys)) in enumerate(series.items()):
        ax.plot(ns, ys, marker="o", ms=4, lw=2, color=PALETTE[i], label=key[0])
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("list size n")
    ax.set_ylabel("comparisons per query (mean)")
    ax.set_title("Search: comparisons per query")
    ax.legend(frameon=False)
    return _save(fig, path)

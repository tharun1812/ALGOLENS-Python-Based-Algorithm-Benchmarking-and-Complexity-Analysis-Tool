"""Animated GIFs of a sorting algorithm at work. Every write to the array is recorded, then sampled down to a few
dozen frames; bars show the values and the most recently written position is highlighted."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

from .generators import make_input                    # noqa: E402
from .instrument import Stats, wrap                   # noqa: E402
from .sorting import SORTS                            # noqa: E402

Frame = tuple[list[int], int | None, int, int]       # (values, last written index, comparisons so far, writes so far)


def record_frames(algorithm: str, values: list[int], max_frames: int = 120) -> list[Frame]:
    """Run the algorithm and capture the array after (a sample of) its writes. The first and last states are always kept."""
    stats = Stats()
    snapshots: list[Frame] = []

    def on_write(arr, index):
        i = index if isinstance(index, int) else None
        snapshots.append(([x.value for x in arr], i, stats.comparisons, stats.writes))

    arr = wrap(values, stats, on_write)
    initial: Frame = ([x.value for x in arr], None, 0, 0)
    SORTS[algorithm].fn(arr)
    if not snapshots:
        return [initial]
    step = max(1, len(snapshots) // max_frames)
    sampled = snapshots[::step]
    if sampled[-1] is not snapshots[-1]:
        sampled.append(snapshots[-1])
    return [initial, *sampled]


def make_gif(algorithm: str, path: str | Path, n: int = 36, distribution: str = "random", seed: int = 3, fps: int = 18) -> Path:
    if algorithm not in SORTS:
        raise ValueError(f"unknown algorithm '{algorithm}'")
    values = make_input(distribution, n, seed)
    frames = record_frames(algorithm, values)
    frames += [frames[-1]] * 14                                      # hold the finished state for a moment
    top = max(values) * 1.08 if values else 1

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.set_xlim(-0.8, n - 0.2)
    ax.set_ylim(0, top)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(False)
    bars = ax.bar(range(n), frames[0][0], color="#0f766e", width=0.85)
    title = ax.set_title("", fontsize=10)

    def draw(k: int):
        data, hot, comparisons, writes = frames[k]
        done = k >= len(frames) - 14
        for i, (bar, v) in enumerate(zip(bars, data)):
            bar.set_height(v)
            bar.set_color("#d97706" if i == hot else ("#15803d" if done else "#0f766e"))
        title.set_text(f"{algorithm.replace('_', ' ')} sort   comparisons {comparisons}   writes {writes}")
        return [*bars, title]

    anim = FuncAnimation(fig, draw, frames=len(frames), blit=False)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    anim.save(path, writer=PillowWriter(fps=fps), dpi=70)
    plt.close(fig)
    return Path(path)

"""Five search algorithms over a sorted TrackedList. Each returns the index of `target`, or -1 if it is absent."""
from __future__ import annotations

from dataclasses import dataclass
from math import isqrt
from typing import Callable

from .instrument import Item, TrackedList


def linear_search(a: TrackedList, target: Item) -> int:
    for i, item in enumerate(a):
        if item == target:
            return i
    return -1


def _lower_bound(a: TrackedList, target: Item, lo: int, hi: int) -> int:
    """First index in [lo, hi) whose element is not smaller than target (about log2(n) comparisons)."""
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def binary_search(a: TrackedList, target: Item) -> int:
    i = _lower_bound(a, target, 0, len(a))
    return i if i < len(a) and a[i] == target else -1


def exponential_search(a: TrackedList, target: Item) -> int:
    """Double the probe position until we pass the target, then binary search the last range."""
    n = len(a)
    if n == 0:
        return -1
    bound = 1
    while bound < n and a[bound] < target:
        bound *= 2
    i = _lower_bound(a, target, bound // 2, min(bound + 1, n))
    return i if i < n and a[i] == target else -1


def jump_search(a: TrackedList, target: Item) -> int:
    """Jump ahead in blocks of about sqrt(n), then scan the one block that can contain the target."""
    n = len(a)
    if n == 0:
        return -1
    block = max(1, isqrt(n))
    prev, step = 0, block
    while a[min(step, n) - 1] < target:
        prev = step
        step += block
        if prev >= n:
            return -1
    for i in range(prev, min(step, n)):
        if a[i] == target:
            return i
        if target < a[i]:
            return -1
    return -1


def interpolation_search(a: TrackedList, target: Item) -> int:
    """Guess where the target sits from its value (good on evenly spread data), then correct."""
    lo, hi = 0, len(a) - 1
    while lo <= hi and not target < a[lo] and not a[hi] < target:
        if a[hi].value == a[lo].value:
            return lo if a[lo] == target else -1
        pos = lo + (target.value - a[lo].value) * (hi - lo) // (a[hi].value - a[lo].value)
        if a[pos] == target:
            return pos
        if a[pos] < target:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1


@dataclass(frozen=True)
class SearchSpec:
    name: str
    fn: Callable[[TrackedList, Item], int]
    max_n: int


SEARCHES: dict[str, SearchSpec] = {s.name: s for s in [
    SearchSpec("linear", linear_search, 16384),
    SearchSpec("binary", binary_search, 131072),
    SearchSpec("exponential", exponential_search, 131072),
    SearchSpec("jump", jump_search, 131072),
    SearchSpec("interpolation", interpolation_search, 131072),
]}

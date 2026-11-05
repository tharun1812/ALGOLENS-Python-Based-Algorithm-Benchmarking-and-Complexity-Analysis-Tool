"""Eleven sorting algorithms, written plainly. Each sorts a TrackedList in place."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .instrument import TrackedList


def bubble_sort(a: TrackedList) -> None:
    """Bubble sort with an early exit when a full pass makes no swap."""
    for end in range(len(a) - 1, 0, -1):
        swapped = False
        for i in range(end):
            if a[i + 1] < a[i]:
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        if not swapped:
            break


def insertion_sort(a: TrackedList) -> None:
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and key < a[j]:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key


def selection_sort(a: TrackedList) -> None:
    n = len(a)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if a[j] < a[smallest]:
                smallest = j
        if smallest != i:
            a[i], a[smallest] = a[smallest], a[i]


def _ciura_gaps(n: int) -> list[int]:
    gaps = [1, 4, 10, 23, 57, 132, 301, 701]
    while gaps[-1] * 2.25 < n:                       # extend Ciura's sequence for larger inputs
        gaps.append(int(gaps[-1] * 2.25))
    return [g for g in reversed(gaps) if g < n] or [1]


def shell_sort(a: TrackedList) -> None:
    n = len(a)
    for gap in _ciura_gaps(n):
        for i in range(gap, n):
            held = a[i]
            j = i
            while j >= gap and held < a[j - gap]:
                a[j] = a[j - gap]
                j -= gap
            a[j] = held


def merge_sort(a: TrackedList) -> None:
    def sort(lo: int, hi: int) -> None:
        if hi - lo < 2:
            return
        mid = (lo + hi) // 2
        sort(lo, mid)
        sort(mid, hi)
        left, right = a[lo:mid], a[mid:hi]           # temporary buffers
        i = j = 0
        k = lo
        while i < len(left) and j < len(right):
            if right[j] < left[i]:                   # take from the left unless the right is strictly smaller: stable
                a[k] = right[j]
                j += 1
            else:
                a[k] = left[i]
                i += 1
            k += 1
        while i < len(left):
            a[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            a[k] = right[j]
            j += 1
            k += 1
    sort(0, len(a))


def quick_sort_naive(a: TrackedList) -> None:
    """Quicksort that always picks the first element as the pivot (Lomuto partition, explicit stack)."""
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        pivot = a[lo]
        boundary = lo
        for j in range(lo + 1, hi + 1):
            if a[j] < pivot:
                boundary += 1
                a[boundary], a[j] = a[j], a[boundary]
        a[lo], a[boundary] = a[boundary], a[lo]
        stack.append((lo, boundary - 1))
        stack.append((boundary + 1, hi))


def quick_sort_median3(a: TrackedList) -> None:
    """Quicksort with a median-of-three pivot and Hoare partitioning, which copes with sorted and repeated data."""
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        x, y, z = a[lo], a[(lo + hi) // 2], a[hi]
        if x < y:
            pivot = y if y < z else (z if x < z else x)
        else:
            pivot = x if x < z else (z if y < z else y)
        i, j = lo - 1, hi + 1
        while True:
            i += 1
            while a[i] < pivot:
                i += 1
            j -= 1
            while pivot < a[j]:
                j -= 1
            if i >= j:
                break
            a[i], a[j] = a[j], a[i]
        stack.append((lo, j))
        stack.append((j + 1, hi))


def heap_sort(a: TrackedList) -> None:
    n = len(a)

    def sift_down(root: int, end: int) -> None:
        while True:
            child = 2 * root + 1
            if child >= end:
                return
            if child + 1 < end and a[child] < a[child + 1]:
                child += 1
            if a[root] < a[child]:
                a[root], a[child] = a[child], a[root]
                root = child
            else:
                return

    for start in range((n - 2) // 2, -1, -1):
        sift_down(start, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(0, end)


def timsort(a: TrackedList) -> None:
    """Python's built-in sort (Timsort). Comparisons are counted through the Item objects."""
    a[:] = sorted(a)


def counting_sort(a: TrackedList) -> None:
    """Counting sort: no comparisons at all, it indexes buckets by value. Stable."""
    if not a:
        return
    low = min(x.value for x in a)
    buckets: list[list] = [[] for _ in range(max(x.value for x in a) - low + 1)]
    for item in a:
        buckets[item.value - low].append(item)
    k = 0
    for bucket in buckets:
        for item in bucket:
            a[k] = item
            k += 1


def radix_sort(a: TrackedList) -> None:
    """LSD radix sort in base 16 for non-negative integers: one stable bucket pass per hex digit."""
    if not a:
        return
    if min(x.value for x in a) < 0:
        raise ValueError("radix_sort needs non-negative integers")
    shift, biggest = 0, max(x.value for x in a)
    while (biggest >> shift) > 0:
        buckets: list[list] = [[] for _ in range(16)]
        for item in a:
            buckets[(item.value >> shift) & 15].append(item)
        k = 0
        for bucket in buckets:
            for item in bucket:
                a[k] = item
                k += 1
        shift += 4


@dataclass(frozen=True)
class SortSpec:
    name: str
    fn: Callable[[TrackedList], None]
    stable: bool
    kind: str            # "comparison" or "non-comparison"
    max_n: int           # largest size used by the experiments (keeps pure-Python runtimes reasonable)


SORTS: dict[str, SortSpec] = {s.name: s for s in [
    SortSpec("bubble", bubble_sort, True, "comparison", 1024),
    SortSpec("insertion", insertion_sort, True, "comparison", 1024),
    SortSpec("selection", selection_sort, False, "comparison", 1024),
    SortSpec("quick_naive", quick_sort_naive, False, "comparison", 1024),
    SortSpec("shell", shell_sort, False, "comparison", 8192),
    SortSpec("merge", merge_sort, True, "comparison", 8192),
    SortSpec("quick_median3", quick_sort_median3, False, "comparison", 8192),
    SortSpec("heap", heap_sort, False, "comparison", 8192),
    SortSpec("timsort", timsort, True, "comparison", 8192),
    SortSpec("counting", counting_sort, True, "non-comparison", 8192),
    SortSpec("radix", radix_sort, True, "non-comparison", 8192),
]}

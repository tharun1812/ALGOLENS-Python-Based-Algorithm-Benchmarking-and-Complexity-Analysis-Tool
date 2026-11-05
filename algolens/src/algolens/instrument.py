"""Instrumentation. Algorithms are written as ordinary Python (using `<`, `==` and indexing); the counting happens
inside the objects they operate on, so the algorithm code stays clean and the counts cannot be forgotten."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass
class Stats:
    comparisons: int = 0
    writes: int = 0

    def reset(self) -> None:
        self.comparisons = self.writes = 0


class Item:
    """An integer value that counts every comparison made on it. `tag` lets tests check stability."""
    __slots__ = ("value", "tag", "stats")

    def __init__(self, value: int, stats: Stats, tag: int = 0):
        self.value, self.tag, self.stats = value, tag, stats

    def __lt__(self, other: "Item") -> bool:
        self.stats.comparisons += 1
        return self.value < other.value

    def __le__(self, other: "Item") -> bool:
        self.stats.comparisons += 1
        return self.value <= other.value

    def __gt__(self, other: "Item") -> bool:
        self.stats.comparisons += 1
        return self.value > other.value

    def __ge__(self, other: "Item") -> bool:
        self.stats.comparisons += 1
        return self.value >= other.value

    def __eq__(self, other: object) -> bool:
        self.stats.comparisons += 1
        return isinstance(other, Item) and self.value == other.value

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Item({self.value})"


class TrackedList(list):
    """A list that counts array writes and can report every change (used for animations).

    Only writes to *this* list are counted. Reading is free, and so is copying a slice into a temporary buffer, so the
    write count means "how many times the main array was modified".
    """

    def __init__(self, items: Iterable[Item], stats: Stats, on_write: Callable[["TrackedList", object], None] | None = None):
        super().__init__(items)
        self.stats = stats
        self.on_write = on_write

    def __setitem__(self, index, value):                                   # type: ignore[override]
        if isinstance(index, slice):
            self.stats.writes += len(range(*index.indices(len(self))))
        else:
            self.stats.writes += 1
        super().__setitem__(index, value)
        if self.on_write is not None:
            self.on_write(self, index)

    @property
    def values(self) -> list[int]:
        return [x.value for x in self]


def wrap(values: Iterable[int], stats: Stats | None = None, on_write=None) -> TrackedList:
    """Turn plain integers into an instrumented list (tags record the original positions)."""
    stats = stats if stats is not None else Stats()
    return TrackedList((Item(v, stats, i) for i, v in enumerate(values)), stats, on_write)

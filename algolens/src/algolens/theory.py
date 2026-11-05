"""What the textbooks say, for the comparison count. Used to check the inferred classes.

Only the standard cases are listed (random, sorted, reversed input). For the others the theory depends on details, so
no expectation is claimed and the report shows a dash instead of a match mark.
"""
from __future__ import annotations

SORT_THEORY: dict[tuple[str, str], str] = {
    ("bubble", "random"): "O(n^2)", ("bubble", "sorted"): "O(n)", ("bubble", "reversed"): "O(n^2)",
    ("insertion", "random"): "O(n^2)", ("insertion", "sorted"): "O(n)", ("insertion", "reversed"): "O(n^2)",
    ("selection", "random"): "O(n^2)", ("selection", "sorted"): "O(n^2)", ("selection", "reversed"): "O(n^2)",
    ("quick_naive", "random"): "O(n log n)", ("quick_naive", "sorted"): "O(n^2)", ("quick_naive", "reversed"): "O(n^2)",
    ("quick_median3", "random"): "O(n log n)", ("quick_median3", "sorted"): "O(n log n)", ("quick_median3", "reversed"): "O(n log n)",
    ("merge", "random"): "O(n log n)", ("merge", "sorted"): "O(n log n)", ("merge", "reversed"): "O(n log n)",
    ("heap", "random"): "O(n log n)", ("heap", "sorted"): "O(n log n)", ("heap", "reversed"): "O(n log n)",
    ("timsort", "random"): "O(n log n)", ("timsort", "sorted"): "O(n)", ("timsort", "reversed"): "O(n)",
}

# For the non-comparison sorts the interesting cost is array writes, not comparisons.
# Radix sort does one pass per digit, so it costs O(n * d) where d = log16(largest key). Our random keys grow with n
# (up to 4n), so d grows like log n and the cost is O(n log n). With only 8 distinct values, d is a constant 1: O(n).
SORT_WRITE_THEORY: dict[tuple[str, str], str] = {
    **{("counting", d): "O(n)" for d in ("random", "sorted", "reversed", "nearly_sorted", "few_unique")},
    **{("radix", d): "O(n log n)" for d in ("random", "sorted", "reversed", "nearly_sorted")},
    ("radix", "few_unique"): "O(n)",
}

SEARCH_THEORY: dict[str, str] = {
    "linear": "O(n)", "binary": "O(log n)", "exponential": "O(log n)", "jump": "O(sqrt n)", "interpolation": "O(log log n)",
}

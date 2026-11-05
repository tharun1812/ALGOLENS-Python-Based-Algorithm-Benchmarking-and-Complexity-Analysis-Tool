import math

import pytest
from hypothesis import given, strategies as st

from algolens.generators import DISTRIBUTIONS, make_input
from algolens.instrument import wrap
from algolens.sorting import SORTS

ALL = list(SORTS)
COMPARISON = [n for n, s in SORTS.items() if s.kind == "comparison"]
STABLE = [n for n, s in SORTS.items() if s.stable]


def run(name, values):
    arr = wrap(values)
    SORTS[name].fn(arr)
    return arr


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("dist", DISTRIBUTIONS)
@pytest.mark.parametrize("n", [0, 1, 2, 3, 17, 200])
def test_every_sort_sorts_every_kind_of_input(name, dist, n):
    values = make_input(dist, n, seed=2) if n else []
    assert run(name, values).values == sorted(values)


@pytest.mark.parametrize("name", ALL)
def test_degenerate_inputs(name):
    for values in ([], [4], [7, 7, 7, 7], [0, 0], [1, 0], list(range(10)), list(range(10, 0, -1)), [3, 1, 3, 1, 3, 1]):
        assert run(name, values).values == sorted(values)


@pytest.mark.parametrize("name", ALL)
@given(st.lists(st.integers(0, 10_000), max_size=120))
def test_result_is_the_sorted_permutation_of_the_input(name, values):
    assert run(name, values).values == sorted(values)


@pytest.mark.parametrize("name", [n for n in ALL if n != "radix"])
@given(st.lists(st.integers(-1000, 1000), max_size=80))
def test_negative_numbers_are_supported_except_by_radix(name, values):
    assert run(name, values).values == sorted(values)


def test_radix_refuses_negative_numbers_instead_of_failing_silently():
    with pytest.raises(ValueError, match="non-negative"):
        run("radix", [3, -1, 2])


@pytest.mark.parametrize("name", STABLE)
@given(st.lists(st.integers(0, 5), min_size=2, max_size=80))
def test_stable_sorts_keep_equal_elements_in_original_order(name, values):
    out = run(name, values)
    for left, right in zip(out, out[1:]):
        if left.value == right.value:
            assert left.tag < right.tag


@pytest.mark.parametrize("n", [2, 5, 33, 100])
def test_exact_comparison_counts(n):
    ascending, descending = list(range(n)), list(range(n, 0, -1))
    assert run("bubble", ascending).stats.comparisons == n - 1             # one clean pass, then it stops
    assert run("insertion", ascending).stats.comparisons == n - 1
    assert run("timsort", ascending).stats.comparisons == n - 1
    assert run("quick_naive", ascending).stats.comparisons == n * (n - 1) // 2       # worst case: pivot is always the minimum
    for values in (ascending, descending, make_input("random", n, 1)):
        assert run("selection", values).stats.comparisons == n * (n - 1) // 2          # independent of the data
    assert run("insertion", descending).stats.comparisons == n * (n - 1) // 2


@pytest.mark.parametrize("n", [16, 100, 500])
def test_comparison_upper_bounds(n):
    values = make_input("random", n, 3)
    assert run("merge", values).stats.comparisons <= n * math.ceil(math.log2(n))
    assert run("heap", values).stats.comparisons <= 2 * n * math.log2(n)
    assert run("quick_median3", values).stats.comparisons <= 4 * n * math.log2(n)


def test_selection_sort_makes_few_writes_and_non_comparison_sorts_make_no_comparisons():
    values = make_input("random", 200, 4)
    assert run("selection", values).stats.writes <= 2 * 199
    for name in ("counting", "radix"):
        arr = run(name, values)
        assert arr.stats.comparisons == 0 and arr.stats.writes >= 200


def test_counting_sort_writes_each_element_once_and_radix_once_per_hex_digit():
    values = [5, 300, 70000, 12]
    assert run("counting", values).stats.writes == 4
    assert run("radix", values).stats.writes == 4 * 5                            # 70000 needs 5 hex digits (0x11170)


def test_quick_naive_degrades_on_repeated_values_but_median3_does_not():
    """With only 8 distinct values the naive pivot choice goes quadratic; compare how the cost GROWS as n quadruples."""
    def cost(name, n):
        return run(name, make_input("few_unique", n, 5)).stats.comparisons

    naive_growth = cost("quick_naive", 1024) / cost("quick_naive", 256)        # roughly 16x if quadratic
    median_growth = cost("quick_median3", 1024) / cost("quick_median3", 256)   # roughly 4.5x if n log n
    assert naive_growth > 2 * median_growth
    assert cost("quick_naive", 512) > 2 * cost("quick_median3", 512)


def test_shell_sort_gap_sequence_is_decreasing_and_ends_in_one():
    from algolens.sorting import _ciura_gaps
    for n in (2, 10, 100, 5000, 100000):
        gaps = _ciura_gaps(n)
        assert gaps == sorted(gaps, reverse=True)
        assert gaps[-1] == 1 and all(g < n for g in gaps)

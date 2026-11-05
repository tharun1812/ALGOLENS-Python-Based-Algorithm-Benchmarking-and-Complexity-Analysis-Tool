import math

import pytest
from hypothesis import given, strategies as st

from algolens.instrument import wrap
from algolens.searching import SEARCHES

NAMES = list(SEARCHES)


def search(name, values, target):
    arr = wrap(values)
    probe = wrap([target], arr.stats)[0]
    arr.stats.reset()
    found = SEARCHES[name].fn(arr, probe)
    return found, arr.stats.comparisons


@pytest.mark.parametrize("name", NAMES)
@given(st.lists(st.integers(0, 500), max_size=60, unique=True).map(sorted), st.integers(-5, 505))
def test_finds_every_present_value_and_rejects_absent_ones(name, values, target):
    found, _ = search(name, values, target)
    assert found == (values.index(target) if target in values else -1)


@pytest.mark.parametrize("name", NAMES)
def test_every_element_is_found_in_lists_of_awkward_sizes(name):
    for n in (1, 2, 3, 4, 7, 8, 9, 15, 16, 17, 100, 1000):
        values = [3 * i + 1 for i in range(n)]
        for i, v in enumerate(values):
            assert search(name, values, v)[0] == i
        for absent in (-1, 0, 2, 3 * n + 5, 3 * n):
            assert search(name, values, absent)[0] == -1


@pytest.mark.parametrize("name", NAMES)
def test_empty_list(name):
    assert search(name, [], 5)[0] == -1


def test_linear_search_cost_is_position_plus_one():
    values = list(range(100))
    assert search("linear", values, 0)[1] == 1 and search("linear", values, 41)[1] == 42 and search("linear", values, 500)[1] == 100


@pytest.mark.parametrize("n", [1, 10, 1000, 65536])
def test_binary_and_exponential_search_are_logarithmic(n):
    values = list(range(0, 2 * n, 2))
    bound = math.ceil(math.log2(n + 1)) + 1
    for target in (values[0], values[n // 2], values[-1], 1, 2 * n + 1):
        assert search("binary", values, target)[1] <= bound
        assert search("exponential", values, target)[1] <= 2 * math.log2(n + 2) + 3


def test_jump_search_cost_is_about_two_square_roots():
    n = 10_000
    values = list(range(n))
    worst = max(search("jump", values, t)[1] for t in (0, 4999, 9999, 5000, 7777))
    assert worst <= 3 * math.isqrt(n)


def test_interpolation_search_is_nearly_instant_on_evenly_spread_values():
    values = list(range(0, 1_000_000, 10))
    assert search("interpolation", values, 500_000)[1] <= 6

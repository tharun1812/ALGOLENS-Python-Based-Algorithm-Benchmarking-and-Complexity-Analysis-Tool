import math

import numpy as np
import pytest
from hypothesis import given, strategies as st

from algolens import complexity as cx
from algolens.generators import DISTRIBUTIONS, make_input, make_sorted_unique


@pytest.mark.parametrize("dist", DISTRIBUTIONS)
def test_generators_are_deterministic_and_have_the_right_length(dist):
    a, b = make_input(dist, 300, seed=4, trial=1), make_input(dist, 300, seed=4, trial=1)
    assert a == b and len(a) == 300
    assert a != make_input(dist, 300, seed=5, trial=1)                      # a different seed gives different data
    assert a != make_input(dist, 300, seed=4, trial=2)                      # and so does a different trial


def test_input_shapes():
    assert make_input("sorted", 200, 1) == sorted(make_input("sorted", 200, 1))
    assert make_input("reversed", 200, 1) == sorted(make_input("reversed", 200, 1), reverse=True)
    assert len(set(make_input("few_unique", 500, 1))) <= 8
    nearly = make_input("nearly_sorted", 400, 2)
    inversions = sum(1 for i in range(399) if nearly[i] > nearly[i + 1])
    assert 0 < inversions < 100                                              # mostly ordered, but not perfectly
    assert make_input("random", 400, 1) != sorted(make_input("random", 400, 1))


def test_unknown_distribution_and_unique_values():
    with pytest.raises(ValueError, match="unknown distribution"):
        make_input("zigzag", 10)
    values = make_sorted_unique(500, seed=1)
    assert values == sorted(set(values)) and len(values) == 500


NS = [64, 128, 256, 512, 1024, 2048, 4096]


@pytest.mark.parametrize("label,f,expected", [
    ("constant", lambda n: 7.0, "O(1)"),
    ("log", lambda n: 4 * math.log2(n), "O(log n)"),
    ("linear", lambda n: 3 * n, "O(n)"),
    ("n log n", lambda n: 2.5 * n * math.log2(n), "O(n log n)"),
    ("n^1.5", lambda n: 0.7 * n ** 1.5, "O(n^1.5)"),
    ("quadratic", lambda n: 0.5 * n * n, "O(n^2)"),
    ("cubic", lambda n: 0.01 * n ** 3, "O(n^3)"),
])
def test_exact_curves_are_classified_correctly(label, f, expected):
    assert cx.fit_complexity(NS, [f(n) for n in NS], cx.SORT_MODELS).best == expected


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("f,expected", [(lambda n: n * math.log2(n), "O(n log n)"), (lambda n: n * n, "O(n^2)"), (lambda n: 2 * n, "O(n)")])
def test_five_percent_noise_does_not_change_the_answer(seed, f, expected):
    rng = np.random.default_rng(seed)
    ys = [f(n) * rng.uniform(0.95, 1.05) for n in NS]
    assert cx.fit_complexity(NS, ys, cx.SORT_MODELS).best == expected


def test_exponent_and_coefficient_are_reported():
    fit = cx.fit_complexity(NS, [0.5 * n * n for n in NS], cx.SORT_MODELS)
    assert fit.exponent == pytest.approx(2.0, abs=1e-6) and fit.r2 == pytest.approx(1.0) and fit.coefficient == pytest.approx(0.5)
    assert fit.scores["O(n^2)"] < fit.scores["O(n)"]


def test_search_models_include_loglog_and_sqrt():
    ns = [256, 1024, 4096, 16384, 65536]
    assert cx.fit_complexity(ns, [3 * math.sqrt(n) for n in ns], cx.SEARCH_MODELS).best == "O(sqrt n)"
    assert cx.fit_complexity(ns, [2 * math.log2(math.log2(n)) for n in ns], cx.SEARCH_MODELS).best == "O(log log n)"


def test_all_zero_measurements_mean_none_and_bad_input_is_rejected():
    assert cx.fit_complexity(NS, [0] * len(NS), cx.SORT_MODELS).best == "none"
    with pytest.raises(ValueError):
        cx.fit_complexity([64, 128], [1, 2], cx.SORT_MODELS)
    with pytest.raises(ValueError):
        cx.fit_complexity([64, 128, 256], [1, 2], cx.SORT_MODELS)


def test_ties_go_to_the_slower_growing_model():
    # almost-linear data that a more complex model also fits: the simpler class is reported
    ys = [n * (1 + 0.001 * math.log2(n)) for n in NS]
    assert cx.fit_complexity(NS, ys, cx.SORT_MODELS).best == "O(n)"


@given(st.floats(0.1, 50), st.sampled_from([0, 1, 2, 3]))
def test_scaling_the_data_never_changes_the_class(scale, which):
    f = [lambda n: n, lambda n: n * math.log2(n), lambda n: n * n, lambda n: math.log2(n)][which]
    base = cx.fit_complexity(NS, [f(n) for n in NS], cx.SORT_MODELS).best
    assert cx.fit_complexity(NS, [scale * f(n) for n in NS], cx.SORT_MODELS).best == base


def test_doubling_ratio():
    assert cx.doubling_ratio([2, 4, 8, 16], [1, 4, 16, 64]) == pytest.approx(4.0)
    assert cx.doubling_ratio([2, 4, 8], [3, 6, 12]) == pytest.approx(2.0)
    assert math.isnan(cx.doubling_ratio([2, 5], [1, 2]))
    assert cx.growth_rank("O(n)", cx.SORT_MODELS) < cx.growth_rank("O(n^2)", cx.SORT_MODELS)

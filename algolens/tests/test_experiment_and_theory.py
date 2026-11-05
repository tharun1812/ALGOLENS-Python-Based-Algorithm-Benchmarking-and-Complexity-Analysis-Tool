import csv
import json

import pytest

from algolens import experiment as ex
from algolens.generators import DISTRIBUTIONS
from algolens.searching import SEARCHES
from algolens.sorting import SORTS, SortSpec
from algolens.theory import SEARCH_THEORY, SORT_THEORY, SORT_WRITE_THEORY


def test_theory_tables_only_mention_real_algorithms_and_inputs():
    for algo, dist in SORT_THEORY:
        assert algo in SORTS and dist in DISTRIBUTIONS and SORTS[algo].kind == "comparison"
    for algo, dist in SORT_WRITE_THEORY:
        assert algo in SORTS and dist in DISTRIBUTIONS and SORTS[algo].kind == "non-comparison"
    assert set(SEARCH_THEORY) == set(SEARCHES)


def test_sizes_double_from_the_start_value():
    assert ex.sizes_for(512) == [64, 128, 256, 512]
    assert ex.sizes_for(1000, start=100) == [100, 200, 400, 800]


def test_run_sorting_records_every_size_and_trial():
    recs = ex.run_sorting(["merge"], ["random", "sorted"], trials=3, max_n=256)
    sizes = [64, 128, 256]
    assert len([r for r in recs if r["distribution"] == "random"]) == 3 * len(sizes)       # 3 trials each
    assert len([r for r in recs if r["distribution"] == "sorted"]) == len(sizes)           # deterministic: 1 trial
    assert all(r["comparisons"] > 0 and r["writes"] > 0 and r["seconds"] >= 0 for r in recs)


def test_runs_are_reproducible_for_a_given_seed():
    a = ex.run_sorting(["heap"], ["random"], trials=2, seed=11, max_n=128)
    b = ex.run_sorting(["heap"], ["random"], trials=2, seed=11, max_n=128)
    c = ex.run_sorting(["heap"], ["random"], trials=2, seed=12, max_n=128)
    key = lambda recs: [(r["n"], r["comparisons"]) for r in recs]
    assert key(a) == key(b) and key(a) != key(c)


def test_a_broken_algorithm_is_caught_not_silently_measured(monkeypatch):
    def broken(arr):
        pass                                                                    # "sorts" by doing nothing
    monkeypatch.setitem(SORTS, "broken", SortSpec("broken", broken, False, "comparison", 128))
    with pytest.raises(AssertionError, match="wrong result"):
        ex.run_sorting(["broken"], ["random"], max_n=128)


def test_small_experiment_matches_textbook_for_the_classic_cases():
    recs = ex.run_sorting(["bubble", "insertion", "quick_naive", "merge", "timsort"], ["random", "sorted"], trials=2, max_n=512)
    rows = {(r["algorithm"], r["distribution"]): r for r in ex.classify_sorting(recs)}
    assert rows[("bubble", "random")]["measured"] == "O(n^2)" and rows[("bubble", "sorted")]["measured"] == "O(n)"
    assert rows[("insertion", "sorted")]["measured"] == "O(n)"
    assert rows[("quick_naive", "sorted")]["measured"] == "O(n^2)" and rows[("quick_naive", "random")]["measured"] == "O(n log n)"
    assert rows[("merge", "sorted")]["measured"] == "O(n log n)"
    assert rows[("timsort", "sorted")]["measured"] == "O(n)" and rows[("timsort", "random")]["measured"] == "O(n log n)"
    assert all(r["match"] for r in rows.values())


def test_non_comparison_sorts_are_judged_by_writes():
    recs = ex.run_sorting(["counting", "radix"], ["random", "few_unique"], trials=1, max_n=1024)
    rows = {(r["algorithm"], r["distribution"]): r for r in ex.classify_sorting(recs)}
    assert all(r["metric"] == "writes" for r in rows.values())
    assert rows[("counting", "random")]["measured"] == "O(n)"
    assert rows[("radix", "few_unique")]["measured"] == "O(n)"            # one hex digit, so one pass
    assert all(r["match"] for r in rows.values())


def test_search_experiment_recovers_the_textbook_classes():
    recs = ex.run_searching(["linear", "binary", "jump"], queries=60, max_n=4096)
    rows = {r["algorithm"]: r for r in ex.classify_searching(recs)}
    assert rows["linear"]["measured"] == "O(n)" and rows["binary"]["measured"] == "O(log n)" and rows["jump"]["measured"] == "O(sqrt n)"
    assert all(r["match"] for r in rows.values())


def test_a_wrong_search_is_caught(monkeypatch):
    monkeypatch.setitem(SEARCHES, "liar", SEARCHES["linear"].__class__("liar", lambda arr, t: -1, 512))
    with pytest.raises(AssertionError, match="wrong answer"):
        ex.run_searching(["liar"], queries=10, max_n=512)


def test_csv_and_json_writers(tmp_path):
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    ex.write_csv(tmp_path / "sub" / "t.csv", rows)
    with open(tmp_path / "sub" / "t.csv", newline="") as fh:
        assert list(csv.DictReader(fh)) == [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]
    ex.write_json(tmp_path / "t.json", {"rows": rows})
    assert json.loads((tmp_path / "t.json").read_text()) == {"rows": rows}

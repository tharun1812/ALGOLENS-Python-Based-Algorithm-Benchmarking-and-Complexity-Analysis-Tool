from algolens.instrument import Item, Stats, TrackedList, wrap


def test_every_comparison_operator_is_counted_once():
    s = Stats()
    a, b = Item(1, s), Item(2, s)
    assert (a < b) and (a <= b) and not (a > b) and not (a >= b) and not (a == b)
    assert s.comparisons == 5


def test_items_with_equal_values_compare_equal_but_arent_hashable():
    s = Stats()
    assert Item(3, s) == Item(3, s)
    try:
        hash(Item(3, s))
    except TypeError:
        pass
    else:
        raise AssertionError("Item should be unhashable because it defines __eq__")


def test_writes_are_counted_for_indexes_and_slices_but_reads_are_free():
    arr = wrap([5, 3, 1])
    _ = arr[0], arr[1:], list(arr)
    assert arr.stats.writes == 0
    arr[0] = arr[2]
    assert arr.stats.writes == 1
    arr[:] = list(reversed(arr))
    assert arr.stats.writes == 4                     # 1 + a 3-element slice
    arr[1:3] = arr[1:3]
    assert arr.stats.writes == 6


def test_swap_counts_two_writes():
    arr = wrap([1, 2])
    arr[0], arr[1] = arr[1], arr[0]
    assert arr.stats.writes == 2 and arr.values == [2, 1]


def test_on_write_callback_receives_the_changed_position():
    seen = []
    arr = wrap([1, 2, 3], on_write=lambda lst, idx: seen.append((idx, lst.values)))
    arr[1] = arr[2]
    assert seen == [(1, [1, 3, 3])]


def test_wrap_tags_record_original_positions_and_share_stats():
    s = Stats()
    arr = wrap([9, 9, 9], s)
    assert [x.tag for x in arr] == [0, 1, 2] and arr.stats is s and isinstance(arr, TrackedList)
    s.reset()
    assert s.comparisons == s.writes == 0

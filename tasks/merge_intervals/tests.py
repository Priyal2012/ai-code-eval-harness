"""Hidden tests for merge_intervals. Imports the candidate as `solution`."""

import random

from solution import merge_intervals


def test_basic_overlap():
    assert merge_intervals([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]


def test_unsorted_input():
    assert merge_intervals([(8, 10), (1, 3), (2, 6)]) == [(1, 6), (8, 10)]


def test_contained_interval():
    assert merge_intervals([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]


def test_edge_touching_intervals_merge():
    assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]


def test_edge_empty_and_single():
    assert merge_intervals([]) == []
    assert merge_intervals([(4, 4)]) == [(4, 4)]


def test_edge_invalid_interval_raises():
    try:
        merge_intervals([(5, 1)])
    except ValueError:
        return
    raise AssertionError("start > end must raise ValueError")


def test_edge_input_not_mutated():
    data = [(3, 4), (1, 2)]
    snapshot = list(data)
    merge_intervals(data)
    assert data == snapshot, "input list was reordered or modified"


def test_edge_negative_values():
    assert merge_intervals([(-5, -1), (-2, 2), (3, 4)]) == [(-5, 2), (3, 4)]


def test_perf_large_input():
    rng = random.Random(11)
    data = [(s, s + rng.randint(0, 50)) for s in (rng.randint(0, 10**7) for _ in range(100_000))]
    merged = merge_intervals(data)
    assert all(a[1] < b[0] for a, b in zip(merged, merged[1:], strict=False))
    assert sum(1 for _ in merged) <= len(data)

"""Hidden tests for two_sum. Imports the candidate as `solution`."""

import random

from solution import two_sum


def test_basic_pair():
    assert two_sum([2, 7, 11, 15], 9) == (0, 1)


def test_pair_not_at_start():
    assert two_sum([3, 2, 4], 6) == (1, 2)


def test_returns_smallest_j():
    # (0, 3) and (1, 2) both sum to 10; j=2 is smaller.
    assert two_sum([1, 4, 6, 9], 10) == (1, 2)


def test_edge_no_solution():
    assert two_sum([1, 2, 3], 100) is None


def test_edge_empty_and_single():
    assert two_sum([], 0) is None
    assert two_sum([5], 5) is None


def test_edge_duplicates():
    assert two_sum([3, 3], 6) == (0, 1)


def test_edge_same_element_not_reused():
    assert two_sum([5, 1], 10) is None


def test_edge_negatives_and_zero():
    assert two_sum([-3, 4, 3, 90], 0) == (0, 2)
    assert two_sum([0, 4, 0], 0) == (0, 2)


def test_perf_large_input():
    # 100k distinct values below 1e6, so no pair can reach 3e6 until the two
    # appended values; the answer is unambiguous and sits at the very end.
    rng = random.Random(7)
    nums = rng.sample(range(1, 10**6), 100_000)
    nums.append(2 * 10**6)
    nums.append(10**6)
    assert two_sum(nums, 3 * 10**6) == (100_000, 100_001)

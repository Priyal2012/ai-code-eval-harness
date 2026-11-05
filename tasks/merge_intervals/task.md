# merge_intervals — merge overlapping closed intervals

Implement `merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]`.

Given closed intervals `[start, end]` in any order, return the minimal list of
non-overlapping intervals that covers the same points, sorted by start.

Requirements

- Intervals that touch (`[1, 3]` and `[3, 5]`) are merged into `[1, 5]`.
- An interval with `start > end` is invalid: raise `ValueError`.
- Input must not be mutated.
- Must handle 10⁵ intervals; aim for O(n log n).

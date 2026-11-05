"""Sort by start, then sweep once: O(n log n)."""


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching closed intervals; returns a new sorted list."""
    for start, end in intervals:
        if start > end:
            raise ValueError(f"invalid interval ({start}, {end}): start > end")

    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            prev_start, prev_end = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged

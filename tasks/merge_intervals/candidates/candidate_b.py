def merge_intervals(intervals):
    """Sorts in place and uses a strict overlap test, so touching intervals stay separate."""
    if not intervals:
        return []
    intervals.sort()
    result = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = result[-1]
        if start < last_end:
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result

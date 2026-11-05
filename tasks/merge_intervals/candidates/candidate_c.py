def merge_intervals(intervals):
    """Repeatedly merges any overlapping pair until nothing changes. Correct, but O(n^2) or worse."""
    for s, e in intervals:
        if s > e:
            raise ValueError("bad interval")
    items = list(intervals)
    changed = True
    while changed:
        changed = False
        out = []
        while items:
            s, e = items.pop()
            merged = False
            for idx, (os_, oe) in enumerate(out):
                if s <= oe and os_ <= e:
                    out[idx] = (min(s, os_), max(e, oe))
                    merged = True
                    changed = True
                    break
            if not merged:
                out.append((s, e))
        items = out
    return sorted(items)

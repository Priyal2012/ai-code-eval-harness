def two_sum(nums, target):
    # Build the index first, then look up complements.
    index = {}
    for i, v in enumerate(nums):
        index[v] = i
    for i, v in enumerate(nums):
        c = target - v
        if c in index:
            return (i, index[c])
    return None

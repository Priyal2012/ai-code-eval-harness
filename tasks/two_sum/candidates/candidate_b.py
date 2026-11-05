def two_sum(nums, target):
    """Brute-force: check every pair. Correct, but O(n^2)."""
    n = len(nums)
    for j in range(n):
        for i in range(j):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None

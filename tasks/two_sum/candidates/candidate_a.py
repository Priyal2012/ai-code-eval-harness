"""Hash-map solution: one pass, O(n) time, O(n) extra space."""


def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return indices (i, j), i < j, with nums[i] + nums[j] == target, else None."""
    seen: dict[int, int] = {}
    for j, value in enumerate(nums):
        complement = target - value
        if complement in seen:
            return seen[complement], j
        # Keep the first index for each value so i is as small as possible.
        seen.setdefault(value, j)
    return None

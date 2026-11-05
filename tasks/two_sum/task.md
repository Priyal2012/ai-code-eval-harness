# two_sum — find two numbers that add up to a target

Implement `two_sum(nums: list[int], target: int) -> tuple[int, int] | None`.

Return the indices `(i, j)` with `i < j` of two **distinct** elements such that
`nums[i] + nums[j] == target`. If several pairs exist, return the one whose `j`
is smallest. Return `None` when no pair exists.

Requirements

- Must handle negative numbers, zeros and duplicate values.
- Must not use the same element twice.
- Should run in O(n) time; inputs may contain up to 10⁵ elements.

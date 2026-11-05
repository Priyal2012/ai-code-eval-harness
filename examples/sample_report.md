# Code evaluation report

_Generated 2026-11-05 16:26 UTC_

## Summary

4 task(s), 12 candidate solution(s).

| Candidate | Tasks | Mean score | Accept | Revise | Reject |
| --- | ---: | ---: | ---: | ---: | ---: |
| candidate_a | 4 | 100.0 | 4 | 0 | 0 |
| candidate_b | 4 | 81.2 | 0 | 4 | 0 |
| candidate_c | 4 | 71.9 | 0 | 2 | 2 |

## Task: `lru_cache`

_lru_cache — a fixed-capacity least-recently-used cache_

| Rank | Candidate | Overall | Grade | Verdict | Correctness | Robustness | Efficiency | Maintainability |
| ---: | --- | ---: | :-: | --- | ---: | ---: | ---: | ---: |
| 1 | `candidate_a` | **100.0** | A | Accept | 100% | 100% | 100% | 100% |
| 2 | `candidate_b` | **85.1** | B | Revise | 100% | 100% | 1% | 100% |
| 3 | `candidate_c` | **67.5** | D | Reject | 50% | 75% | 100% | 75% |

### `candidate_a` — 100.0 (Accept)

4/4 core tests pass, 4/4 edge-case tests pass, 0 static findings, max complexity 3. Ready to merge.

**Reviewer notes**

- [efficiency] All 1 performance test(s) pass within the time limit.

### `candidate_b` — 85.1 (Revise)

4/4 core tests pass, 4/4 edge-case tests pass, 0 static findings, max complexity 3. Close — fix the failing cases and address the findings before merging.

**Reviewer notes**

- [efficiency] `test_perf_many_operations` timeout — exceeded 5.0s

### `candidate_c` — 67.5 (Reject)

2/4 core tests pass, 3/4 edge-case tests pass, 1 static finding, max complexity 2. Not mergeable in its current form.

**Reviewer notes**

- [correctness] `test_get_refreshes_recency` failed — assertion failed: `assert c.get("b") is None`
- [correctness] `test_put_updates_existing_and_refreshes` failed — assertion failed: `assert c.get("a") == 10`
- [robustness] `test_edge_invalid_capacity` failed — LRUCache(0) should raise ValueError
- [efficiency] All 1 performance test(s) pass within the time limit.
- [maintainability] L13 E001: bare `except:` also catches KeyboardInterrupt/SystemExit

## Task: `merge_intervals`

_merge_intervals — merge overlapping closed intervals_

| Rank | Candidate | Overall | Grade | Verdict | Correctness | Robustness | Efficiency | Maintainability |
| ---: | --- | ---: | :-: | --- | ---: | ---: | ---: | ---: |
| 1 | `candidate_a` | **100.0** | A | Accept | 100% | 100% | 100% | 100% |
| 2 | `candidate_c` | **85.1** | B | Revise | 100% | 100% | 1% | 100% |
| 3 | `candidate_b` | **76.8** | C | Revise | 100% | 40% | 25% | 100% |

### `candidate_a` — 100.0 (Accept)

3/3 core tests pass, 5/5 edge-case tests pass, 0 static findings, max complexity 6. Ready to merge.

**Reviewer notes**

- [efficiency] All 1 performance test(s) pass within the time limit.

### `candidate_c` — 85.1 (Revise)

3/3 core tests pass, 5/5 edge-case tests pass, 0 static findings, max complexity 9. Close — fix the failing cases and address the findings before merging.

**Reviewer notes**

- [efficiency] `test_perf_large_input` timeout — exceeded 5.0s

### `candidate_b` — 76.8 (Revise)

3/3 core tests pass, 2/5 edge-case tests pass, 0 static findings, max complexity 4. Close — fix the failing cases and address the findings before merging.

**Reviewer notes**

- [robustness] `test_edge_input_not_mutated` failed — input list was reordered or modified
- [robustness] `test_edge_invalid_interval_raises` failed — start > end must raise ValueError
- [robustness] `test_edge_touching_intervals_merge` failed — assertion failed: `assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]`
- [efficiency] `test_perf_large_input` failed — assertion failed: `assert all(a[1] < b[0] for a, b in zip(merged, merged[1:], strict=False))`

## Task: `parse_log_line`

_parse_log_line — parse one line of an access log_

| Rank | Candidate | Overall | Grade | Verdict | Correctness | Robustness | Efficiency | Maintainability |
| ---: | --- | ---: | :-: | --- | ---: | ---: | ---: | ---: |
| 1 | `candidate_a` | **100.0** | A | Accept | 100% | 100% | 100% | 100% |
| 2 | `candidate_b` | **78.0** | C | Revise | 100% | 60% | 7% | 100% |
| 3 | `candidate_c` | **70.0** | C | Revise | 100% | 60% | 35% | 39% |

### `candidate_a` — 100.0 (Accept)

3/3 core tests pass, 5/5 edge-case tests pass, 0 static findings, max complexity 5. Ready to merge.

### `candidate_b` — 78.0 (Revise)

3/3 core tests pass, 3/5 edge-case tests pass, 0 static findings, max complexity 5. Close — fix the failing cases and address the findings before merging.

**Reviewer notes**

- [robustness] `test_edge_malformed_raises` failed — expected ValueError for '10.0.0.7 - alice [05/Nov/2026:10:15:32 +0000] "GET /api/items?page=2 HTTP/1.1" 200 5123 "https://example.com/" '
- [robustness] `test_edge_referrer_with_spaces` failed — assertion failed: `assert rec["referrer"] == "https://example.com/search?q=blue widgets"`

### `candidate_c` — 70.0 (Revise)

3/3 core tests pass, 3/5 edge-case tests pass, 6 static findings, max complexity 6. Close — fix the failing cases and address the findings before merging.

**Reviewer notes**

- [robustness] `test_edge_malformed_raises` failed — expected ValueError for ''
- [robustness] `test_edge_no_partial_result_on_bad_status` failed — non-numeric status must raise ValueError
- [maintainability] L2 W008: import `sys` is unused
- [maintainability] L3 W008: import `os` is unused
- [maintainability] L6 I007: public function `parse_log_line` has no docstring
- [maintainability] L6 W003: `parse_log_line` has a mutable default argument
- [maintainability] L31 I009: `print` in library code; prefer returning values or logging
- [maintainability] L33 E001: bare `except:` also catches KeyboardInterrupt/SystemExit

## Task: `two_sum`

_two_sum — find two numbers that add up to a target_

| Rank | Candidate | Overall | Grade | Verdict | Correctness | Robustness | Efficiency | Maintainability |
| ---: | --- | ---: | :-: | --- | ---: | ---: | ---: | ---: |
| 1 | `candidate_a` | **100.0** | A | Accept | 100% | 100% | 100% | 100% |
| 2 | `candidate_b` | **85.1** | B | Revise | 100% | 100% | 1% | 100% |
| 3 | `candidate_c` | **65.0** | D | Reject | 33% | 80% | 97% | 97% |

### `candidate_a` — 100.0 (Accept)

3/3 core tests pass, 5/5 edge-case tests pass, 0 static findings, max complexity 3. Ready to merge.

**Reviewer notes**

- [efficiency] All 1 performance test(s) pass within the time limit.

### `candidate_b` — 85.1 (Revise)

3/3 core tests pass, 5/5 edge-case tests pass, 0 static findings, max complexity 4. Close — fix the failing cases and address the findings before merging.

**Reviewer notes**

- [efficiency] `test_perf_large_input` timeout — exceeded 5.0s

### `candidate_c` — 65.0 (Reject)

1/3 core tests pass, 4/5 edge-case tests pass, 1 static finding, max complexity 4. Not mergeable in its current form.

**Reviewer notes**

- [correctness] `test_pair_not_at_start` failed — assertion failed: `assert two_sum([3, 2, 4], 6) == (1, 2)`
- [correctness] `test_returns_smallest_j` failed — assertion failed: `assert two_sum([1, 4, 6, 9], 10) == (1, 2)`
- [robustness] `test_edge_same_element_not_reused` failed — assertion failed: `assert two_sum([5, 1], 10) is None`
- [efficiency] All 1 performance test(s) pass within the time limit.
- [maintainability] L1 I007: public function `two_sum` has no docstring

"""Hidden tests for LRUCache. Imports the candidate as `solution`."""

from solution import LRUCache


def test_put_get():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    assert c.get("b") == 2


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts "a"
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # "a" is now most recent
    c.put("c", 3)  # should evict "b"
    assert c.get("b") is None
    assert c.get("a") == 1


def test_put_updates_existing_and_refreshes():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # update counts as use
    c.put("c", 3)  # evicts "b"
    assert c.get("a") == 10
    assert c.get("b") is None
    assert len(c) == 2


def test_edge_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") is None
    assert c.get("b") == 2


def test_edge_invalid_capacity():
    for bad in (0, -1):
        try:
            LRUCache(bad)
        except ValueError:
            continue
        raise AssertionError(f"LRUCache({bad}) should raise ValueError")


def test_edge_missing_key():
    c = LRUCache(3)
    assert c.get("nope") is None
    assert len(c) == 0


def test_edge_falsy_values_are_stored():
    c = LRUCache(2)
    c.put("zero", 0)
    c.put("empty", "")
    assert c.get("zero") == 0
    assert c.get("empty") == ""


def test_perf_many_operations():
    n = 400_000
    capacity = 20_000
    c = LRUCache(capacity)
    for i in range(n):
        c.put(i, i)
        if i % 3 == 0:
            c.get(i - 500)
    assert len(c) == capacity
    assert c.get(n - 1) == n - 1
    assert c.get(0) is None

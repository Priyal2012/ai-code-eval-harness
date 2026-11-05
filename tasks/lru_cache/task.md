# lru_cache — a fixed-capacity least-recently-used cache

Implement a class `LRUCache(capacity: int)` with:

- `get(key) -> value | None` — return the value and mark the key as most recently used.
- `put(key, value) -> None` — insert or update; if the cache is over capacity,
  evict the least recently used key.
- `__len__` — number of stored keys.

Requirements

- `capacity` must be a positive integer; raise `ValueError` otherwise.
- Updating an existing key via `put` counts as a use.
- `get` and `put` must be O(1) on average; the cache may see 10⁵+ operations.

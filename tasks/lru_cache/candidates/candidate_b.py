class LRUCache:
    """Keeps a list of keys ordered by recency. Simple, but list.remove is O(n)."""

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.values = {}
        self.order = []  # least recent first

    def get(self, key):
        if key in self.values:
            self.order.remove(key)
            self.order.append(key)
            return self.values[key]
        return None

    def put(self, key, value):
        if key in self.values:
            self.order.remove(key)
        self.values[key] = value
        self.order.append(key)
        if len(self.order) > self.capacity:
            oldest = self.order.pop(0)
            del self.values[oldest]

    def __len__(self):
        return len(self.values)

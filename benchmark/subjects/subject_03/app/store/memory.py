"""Tiny in-memory store used by the catalog service."""


class MemoryStore:
    def __init__(self):
        self._items = {}

    def insert(self, key, value):
        self._items[key] = value
        return value

    def get(self, key, default=None):
        return self._items.get(key, default)

    def size(self):
        return len(self._items)

    def keys(self):
        return sorted(self._items)

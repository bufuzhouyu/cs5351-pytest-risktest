"""Catalog service built on the text helpers and the memory store."""

from app.core.textx import slugify, titleize
from app.store.memory import MemoryStore


class Catalog:
    def __init__(self):
        self.store = MemoryStore()

    def register(self, name, price):
        key = slugify(name)
        return self.store.insert(key, {"name": titleize(name), "price": price})

    def price_of(self, name):
        entry = self.store.get(slugify(name))
        return entry["price"] if entry else 0

    def count(self):
        return self.store.size()

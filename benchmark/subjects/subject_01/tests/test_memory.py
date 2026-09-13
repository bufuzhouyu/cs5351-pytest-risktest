from app.store.memory import MemoryStore


def test_insert_and_get():
    store = MemoryStore()
    store.insert("a", 1)
    assert store.get("a") == 1


def test_default_value():
    assert MemoryStore().get("missing", 0) == 0


def test_size_and_keys():
    store = MemoryStore()
    store.insert("b", 2)
    store.insert("a", 1)
    assert store.size() == 2
    assert store.keys() == ["a", "b"]

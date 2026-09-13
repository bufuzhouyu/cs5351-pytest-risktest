from app.core.textx import normalize, slugify, titleize


def test_normalize():
    assert normalize("  a   b ") == "a b"


def test_slugify():
    assert slugify("Hello World") == "hello-world"


def test_titleize():
    assert titleize("hello wide world") == "Hello Wide World"

from app.core.mathx import add, clamp, mul, with_tax


def test_add():
    assert add(2, 3) == 5


def test_mul():
    assert mul(4, 5) == 20


def test_clamp():
    assert clamp(11, 0, 10) == 10
    assert clamp(-1, 0, 10) == 0
    assert clamp(5, 0, 10) == 5


def test_with_tax():
    assert with_tax(100) == round(100 * 1.11, 2)

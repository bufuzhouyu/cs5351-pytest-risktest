from tests.support import busy

from app.features.feature_01 import WEIGHT, compute, normalize_total, spread, top


def test_compute():
    busy()
    assert compute([1, 2, 3]) == 30


def test_compute_empty():
    busy()
    assert compute([]) == 0


def test_normalize_total():
    busy()
    assert normalize_total([6, 9, 3]) == 30.0


def test_top_returns_descending_prefix():
    busy()
    assert top([1, 5, 3, 4, 2]) == [5, 4, 3]


def test_spread():
    busy()
    assert spread([2, 9, 4]) == 7


def test_spread_of_empty():
    busy()
    assert spread([]) == 0


def test_weight_is_positive():
    busy()
    assert WEIGHT > 0


def test_compute_is_linear():
    busy()
    assert compute([2, 4]) == compute([4, 2])

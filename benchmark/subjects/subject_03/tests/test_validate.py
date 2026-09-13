import pytest

from app.utils.validate import bounded_quantity, is_positive, validate_line


def test_is_positive():
    assert is_positive(1) is True


def test_bounded_quantity_clamps():
    assert bounded_quantity(50, 10) == 10


def test_bounded_quantity_rejects_non_positive():
    with pytest.raises(ValueError):
        bounded_quantity(0)


def test_validate_line():
    assert validate_line({"quantity": 2, "price": 3}) is True
    assert validate_line({"quantity": 0, "price": 3}) is False

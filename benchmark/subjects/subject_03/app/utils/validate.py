"""Validation helpers."""

from app.core.mathx import clamp


def is_positive(value):
    return value > 0


def bounded_quantity(value, limit=100):
    if not is_positive(value):
        raise ValueError("quantity must be positive")
    return int(clamp(value, 1, limit))


def validate_line(item):
    quantity = item.get("quantity", 0)
    if not is_positive(quantity):
        return False
    return item.get("price", 0) >= 0

"""Numeric helpers used across the services."""

TAX_RATE = 0.13
CURRENCY_SCALE = 100


def add(a, b):
    return a + b


def mul(a, b):
    return a * b


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def with_tax(amount):
    return round(amount * (1 + TAX_RATE), 2)

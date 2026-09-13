"""Generated feature module 1 (owned by the feature_01 unit)."""

from app.core.mathx import add, mul

WEIGHT = 5


def compute(values):
    total = 0
    for value in values:
        total = add(total, mul(value, WEIGHT))
    return total


def normalize_total(values):
    return round(compute(values) / max(len(values), 1), 3)


def top(values, count=3):
    return sorted(values, reverse=True)[:count]


def spread(values):
    if not values:
        return 0
    return max(values) - min(values)

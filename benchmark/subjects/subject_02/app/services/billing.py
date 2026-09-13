"""Billing service."""

from app.core.mathx import add, with_tax
from app.utils.validate import validate_line

DISCOUNT = 0.05


def subtotal(items):
    total = 0
    for item in items:
        if not validate_line(item):
            continue
        total = add(total, item["price"] * item["quantity"])
    return total


def discounted_total(items):
    total = subtotal(items)
    if total > 100:
        total = total * (1 - DISCOUNT)
    return round(total, 2)


def total_with_tax(items):
    return with_tax(discounted_total(items))

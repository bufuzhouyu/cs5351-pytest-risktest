from app.services.billing import discounted_total, subtotal, total_with_tax


def test_subtotal_skips_invalid_lines():
    items = [{"price": 10, "quantity": 2}, {"price": 5, "quantity": 0}]
    assert subtotal(items) == 20


def test_subtotal_adds_lines():
    items = [{"price": 3, "quantity": 3}, {"price": 2, "quantity": 1}]
    assert subtotal(items) == 11


def test_discount_applies_above_threshold():
    items = [{"price": 60, "quantity": 2}]
    assert discounted_total(items) == round(120 * 0.95, 2)


def test_total_with_tax():
    items = [{"price": 10, "quantity": 1}]
    assert total_with_tax(items) == round(10 * 1.11, 2)

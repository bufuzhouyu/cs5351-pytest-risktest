from app.services.reports import biggest, cheap_items, summary


def test_cheap_items():
    items = [{"price": 5, "quantity": 1}, {"price": 50, "quantity": 1}]
    assert cheap_items(items, 10) == [{"price": 5, "quantity": 1}]


def test_summary():
    items = [{"price": 20, "quantity": 2}]
    assert summary(items)["total"] == 40


def test_biggest():
    items = [{"price": 5, "quantity": 1}, {"price": 9, "quantity": 1}]
    assert biggest(items)["price"] == 9


def test_biggest_of_empty_list():
    assert biggest([]) is None
